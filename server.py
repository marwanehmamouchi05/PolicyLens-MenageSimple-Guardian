"""Local-only HTTP adapter, derived from the original standard-library server."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from pathlib import Path
import argparse, json, threading
from guardian import Guardian, scenario, report
from report_fr import export_data

ROOT=Path(__file__).resolve().parent
LOCK=threading.RLock()
APP=None
class LocalServer(ThreadingHTTPServer):
    allow_reuse_address=True
class Handler(BaseHTTPRequestHandler):
    def send_error(self,code,message=None,explain=None):
        return self.send({'error':'Cette demande ne peut pas être traitée. Vérifiez l’adresse et le type de demande.'},code)
    def setup(self):super().setup();self.connection.settimeout(10)
    def send(self,body,status=200,mime='application/json; charset=utf-8',download=None):
        payload=body if isinstance(body,bytes) else (body.encode('utf-8') if isinstance(body,str) else json.dumps(body,ensure_ascii=False).encode('utf-8'))
        self.send_response(status)
        for k,v in [('Content-Type',mime),('Content-Length',str(len(payload))),('Cache-Control','no-store'),('X-Content-Type-Options','nosniff'),('Referrer-Policy','no-referrer'),('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")]:self.send_header(k,v)
        if download:self.send_header('Content-Disposition',f'attachment; filename="{download}"')
        self.end_headers();self.wfile.write(payload)
    def allowed(self):
        if self.headers.get('Host') not in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'):return False
        origin=self.headers.get('Origin')
        return not origin or origin in (f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}')
    def do_GET(self):
        if not self.allowed():return self.send({'error':'Accès autorisé uniquement depuis cette application locale.'},403)
        path=urlsplit(self.path).path
        if path=='/favicon.ico':return self.send(b'',204,'image/x-icon')
        with LOCK:
            if path=='/api/state':return self.send(APP.view())
            if path=='/impact/api/state':
                from impact_integration import action
                return self.send(action(APP,'state',{}))
            if path=='/api/export':return self.send(export_data(APP.view()),download='rapport-PolicyLens.json')
            if path=='/report':return self.send(report(APP.view()),mime='text/html; charset=utf-8')
            if path=='/api/health':return self.send(dict(ok=True,mode='local-curated-snapshot',version='1.0'))
        static={'/':'index.html','/index.html':'index.html','/app.js':'app.js','/style.css':'style.css','/impact.js':'impact.js','/navigation.js':'navigation.js','/graph-explorer.js':'graph-explorer.js'}
        if path in static:
            name=static[path];mime='text/html' if name.endswith('html') else 'text/javascript' if name.endswith('js') else 'text/css'
            return self.send((ROOT/name).read_bytes(),mime=mime+'; charset=utf-8')
        return self.send({'error':'Page ou ressource introuvable.'},404)
    def do_POST(self):
        if not self.allowed():return self.send({'error':'Accès autorisé uniquement depuis cette application locale.'},403)
        try:
            try:n=int(self.headers.get('Content-Length','0'))
            except ValueError:raise ValueError('La taille de la demande est invalide.') from None
            if not 0<n<=20000:raise ValueError('La demande doit contenir de 1 à 20 000 octets.')
            data=json.loads(self.rfile.read(n))
            if not isinstance(data,dict):raise ValueError('Les données doivent être présentées sous forme d’objet JSON.')
            with LOCK:
                path=urlsplit(self.path).path
                if path=='/api/snapshot':value=APP.change(data)
                elif path=='/api/information':value=APP.information(data)
                elif path=='/api/review':value=APP.review(data)
                elif path=='/api/scenario':value=scenario(data)
                elif path=='/api/recheck':value=APP.view()
                elif path.startswith('/impact/api/') and path.rsplit('/',1)[-1] in ('impact','add','simulate','reset','report'):
                    from impact_integration import action
                    value=action(APP,path.rsplit('/',1)[-1],data)
                else:return self.send({'error':'Page ou ressource introuvable.'},404)
            return self.send(value)
        except (json.JSONDecodeError,UnicodeDecodeError,RecursionError):return self.send({'error':'Les données JSON sont illisibles. Vérifiez le formulaire.'},400)
        except KeyError:return self.send({'error':'Le formulaire est incomplet. Renseignez tous les champs nécessaires.'},400)
        except TypeError:return self.send({'error':'Le format des données est incorrect. Vérifiez les champs du formulaire.'},400)
        except ValueError as e:return self.send({'error':str(e)},400)
        except OSError:return self.send({'error':'Enregistrement local impossible. Vérifiez les droits d’accès au dossier de l’application.'},500)
    def log_message(self,*args):pass

if __name__=='__main__':
    p=argparse.ArgumentParser(description='Démarrer la démonstration locale PolicyLens.');p.add_argument('--port',type=int,default=8879);p.add_argument('--ephemeral',action='store_true',help='Démarrer sans charger ni conserver les décisions locales')
    args=p.parse_args();APP=Guardian(None if args.ephemeral else ROOT/'local-state.json')
    server=LocalServer(('127.0.0.1',args.port),Handler)
    print(f'PolicyLens Guardian : http://127.0.0.1:{args.port} (Ctrl+C pour arrêter)',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
