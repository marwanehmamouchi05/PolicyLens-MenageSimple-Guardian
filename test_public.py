import http.cookiejar,json,threading,unittest,urllib.request,urllib.error,os
from unittest.mock import patch
import public_server as pub
import server
from guardian import SUGGESTION
class PublicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch=patch.dict(os.environ,LOCAL_PUBLIC_TEST='1');cls.patch.start()
        cls.previous=server.APP;server.APP=pub.SessionProxy();pub._sessions.clear();pub._rates.clear()
        cls.http=pub.PublicServer(('127.0.0.1',0),pub.Handler);cls.base=f'http://127.0.0.1:{cls.http.server_port}'
        cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown();cls.http.server_close();cls.thread.join();server.APP=cls.previous;cls.patch.stop()
    def client(self):return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def req(self,c,path,data=None,headers=None):
        r=urllib.request.Request(self.base+path,data=json.dumps(data).encode() if data is not None else None,headers=headers or {})
        return c.open(r,timeout=5)
    def test_browser_sessions_are_isolated(self):
        a,b=self.client(),self.client()
        with self.req(a,'/api/snapshot',dict(text=SUGGESTION,scope='regular',confirmed=True)) as r:self.assertEqual(json.load(r)['revision'],1)
        with self.req(b,'/api/state') as r:self.assertEqual(json.load(r)['revision'],0)
        with self.req(a,'/api/state') as r:self.assertEqual(json.load(r)['revision'],1)
    def test_reset_only_affects_current_session(self):
        a,b=self.client(),self.client()
        for c in (a,b):self.req(c,'/api/snapshot',dict(text=SUGGESTION,scope='regular',confirmed=True)).close()
        with self.req(a,'/api/reset',{}) as r:self.assertEqual(json.load(r)['revision'],0)
        with self.req(b,'/api/state') as r:self.assertEqual(json.load(r)['revision'],1)
    def test_cookie_security_and_health(self):
        with patch.dict(os.environ,LOCAL_PUBLIC_TEST='0'):
            with self.req(self.client(),'/api/state') as r:
                cookie=r.headers['Set-Cookie'];self.assertIn('HttpOnly',cookie);self.assertIn('Secure',cookie);self.assertIn('SameSite=Strict',cookie)
        with self.req(self.client(),'/api/health') as r:self.assertEqual(json.load(r),{'ok':True})
    def test_wrong_origin_and_private_files_denied(self):
        with self.assertRaises(urllib.error.HTTPError) as e:self.req(self.client(),'/api/recheck',{},dict(Origin='https://unrelated.invalid'))
        self.assertEqual(e.exception.code,403)
        with self.assertRaises(urllib.error.HTTPError) as e:self.req(self.client(),'/public_server.py')
        self.assertEqual(e.exception.code,404)
    def test_rate_limit(self):
        key=pub.hashlib.sha256(b'127.0.0.1').hexdigest()
        try:
            pub._rates[key]=(pub.time.monotonic(),pub.LIMIT)
            with self.assertRaises(urllib.error.HTTPError) as e:self.req(self.client(),'/api/state')
            self.assertEqual(e.exception.code,429)
        finally:pub._rates.pop(key,None)
if __name__=='__main__':unittest.main(verbosity=2)
