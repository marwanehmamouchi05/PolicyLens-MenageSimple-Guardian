"""Bounded public demo adapter; the original localhost server stays unchanged."""
from collections import OrderedDict
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import urlsplit
import os,secrets,threading,time,hashlib,json
import server
from guardian import Guardian

ROOT=Path(__file__).resolve().parent
TTL=1800
MAX_SESSIONS=128
LIMIT=120
_local=threading.local()
_lock=threading.RLock()
_sessions=OrderedDict()
_rates=OrderedDict()

class SessionProxy:
    def __getattr__(self,name):return getattr(_local.app,name)
    def view(self):
        state=_local.app.view();state['public_demo']=True;return state

class PublicServer(server.LocalServer):
    daemon_threads=True
    request_queue_size=16
    def __init__(self,*args,**kwargs):
        self.slots=threading.BoundedSemaphore(16)
        super().__init__(*args,**kwargs)
    def process_request(self,request,address):
        if not self.slots.acquire(False):
            try:request.sendall(b'HTTP/1.1 503 Service Unavailable\r\nContent-Length: 0\r\nConnection: close\r\n\r\n')
            finally:self.shutdown_request(request)
            return
        try:super().process_request(request,address)
        except Exception:self.slots.release();raise
    def process_request_thread(self,*args):
        try:super().process_request_thread(*args)
        finally:self.slots.release()

class Handler(server.Handler):
    def allowed(self):
        host=self.headers.get('Host','').lower()
        name=host.split(':')[0]
        configured=os.getenv('PUBLIC_HOST','').lower()
        if name not in ('localhost','127.0.0.1',configured) and not name.endswith('.awsapprunner.com'):return False
        origin=self.headers.get('Origin')
        return not origin or origin in (f'https://{host}',f'http://{host}' if name in ('localhost','127.0.0.1') else '')
    def prepare(self):
        self.new_cookie=None
        if not self.allowed():self.send({'error':'Accès non autorisé depuis cette origine.'},403);return False
        now=time.monotonic();ip=self.client_address[0]
        # The trusted HTTPS reverse proxy supplies the original client address.
        if self.headers.get('X-Forwarded-For'):ip=self.headers['X-Forwarded-For'].split(',')[0].strip()[:64]
        key=hashlib.sha256(ip.encode()).hexdigest()
        with _lock:
            window,count=_rates.get(key,(now,0))
            if now-window>=60:window,count=now,0
            _rates[key]=(window,count+1);_rates.move_to_end(key)
            while len(_rates)>512:_rates.popitem(last=False)
            if count>=LIMIT:self.send({'error':'Trop de demandes. Patientez une minute avant de réessayer.'},429);return False
            expired=[sid for sid,(t,app) in _sessions.items() if now-t>TTL]
            for sid in expired:_sessions.pop(sid,None)
            cookie=SimpleCookie()
            try:cookie.load(self.headers.get('Cookie',''))
            except Exception:pass
            cookie_name='policylens_session' if os.getenv('LOCAL_PUBLIC_TEST')=='1' else '__Host-policylens_session'
            sid=cookie[cookie_name].value if cookie_name in cookie else ''
            if sid not in _sessions:
                if len(_sessions)>=MAX_SESSIONS:self.send({'error':'La démonstration est momentanément complète. Réessayez plus tard.'},503);return False
                sid=secrets.token_urlsafe(32);_sessions[sid]=(now,Guardian());self.new_cookie=sid
            _local.app=_sessions[sid][1];_sessions[sid]=(now,_local.app);self.sid=sid
        return True
    def send(self,body,status=200,mime='application/json; charset=utf-8',download=None):
        # Match the local adapter's security headers, adding a private demo cookie.
        payload=body if isinstance(body,bytes) else (body.encode('utf-8') if isinstance(body,str) else json.dumps(body,ensure_ascii=False).encode())
        self.send_response(status)
        headers={'Content-Type':mime,'Content-Length':str(len(payload)),'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"}
        for k,v in headers.items():self.send_header(k,v)
        if getattr(self,'new_cookie',None):
            secure='' if os.getenv('LOCAL_PUBLIC_TEST')=='1' else '; Secure'
            name='policylens_session' if os.getenv('LOCAL_PUBLIC_TEST')=='1' else '__Host-policylens_session'
            self.send_header('Set-Cookie',f'{name}={self.new_cookie}; Path=/; HttpOnly; SameSite=Strict; Max-Age={TTL}{secure}')
        if download:self.send_header('Content-Disposition',f'attachment; filename="{download}"')
        self.end_headers();self.wfile.write(payload)
    def do_GET(self):
        if urlsplit(self.path).path=='/api/health':return self.send({'ok':True})
        if self.prepare():return super().do_GET()
    def do_POST(self):
        if not self.prepare():return
        with _lock:
            if urlsplit(self.path).path=='/api/reset':
                _local.app=Guardian();_sessions[self.sid]=(time.monotonic(),_local.app)
                return self.send(_local.app.view())
            if sum(len(_local.app.state.get(k,[])) for k in ('history','reviews','information_history'))>=150:
                return self.send({'error':'Limite de la session atteinte. Réinitialisez votre démonstration.'},429)
        return super().do_POST()

def main():
    server.APP=SessionProxy()
    port=int(os.getenv('PORT','8080'))
    http=PublicServer((os.getenv('BIND_HOST','0.0.0.0'),port),Handler)
    print('PolicyLens : démonstration publique démarrée.',flush=True)
    try:http.serve_forever()
    except KeyboardInterrupt:pass
    finally:http.server_close()

if __name__=='__main__':main()
