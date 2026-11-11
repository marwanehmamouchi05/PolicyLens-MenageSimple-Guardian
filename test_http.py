import json, threading, unittest, urllib.request, urllib.error
import server
from guardian import Guardian, SUGGESTION

class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        server.APP=Guardian();cls.http=server.LocalServer(('127.0.0.1',0),server.Handler)
        cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.http.server_port}'
    @classmethod
    def tearDownClass(cls):cls.http.shutdown();cls.http.server_close();cls.thread.join()
    def request(self,path,data=None,headers=None):
        r=urllib.request.Request(self.base+path,data=json.dumps(data).encode() if data is not None else None,headers=headers or {})
        try:
            with urllib.request.urlopen(r,timeout=5) as out:return out.status,out.headers,out.read()
        except urllib.error.HTTPError as e:return e.code,e.headers,e.read()
    def test_dashboard_and_static_assets(self):
        for path,kind in (('/','text/html'),('/app.js','text/javascript'),('/style.css','text/css')):
            code,headers,body=self.request(path);self.assertEqual(code,200);self.assertIn(kind,headers['Content-Type']);self.assertTrue(body)
    def test_private_files_are_not_served(self):
        for path in ('/sources.json','/local-state.json','/server.py','/../server.py'):
            self.assertEqual(self.request(path)[0],404)
    def test_cross_origin_mutation_rejected(self):
        self.assertEqual(self.request('/api/recheck',{},dict(Origin='https://unrelated.invalid'))[0],403)
    def test_untrusted_host_rejected(self):
        self.assertEqual(self.request('/api/state',headers=dict(Host='unrelated.invalid'))[0],403)
    def test_invalid_mutation_rejected(self):
        self.assertEqual(self.request('/api/snapshot',dict(text='',scope='regular',confirmed=True))[0],400)
    def test_http_workflow_and_exports(self):
        code,_,body=self.request('/api/snapshot',dict(text=SUGGESTION,scope='regular',confirmed=True));self.assertEqual(code,200)
        state=json.loads(body);self.assertEqual(state['findings'][0]['status'],'Resolved in simulation')
        f=state['findings'][0]
        self.assertEqual(self.request('/api/review',dict(id=f['id'],fingerprint=f['fingerprint'],decision='Accept',wording=SUGGESTION))[0],200)
        code,h,b=self.request('/report');self.assertEqual(code,200);self.assertIn('Résolu dans la simulation'.encode(),b);self.assertIn('Décision du réviseur :</b> Accepter'.encode(),b)
        code,h,b=self.request('/api/export');self.assertIn('attachment',h['Content-Disposition']);self.assertTrue(json.loads(b)['historique_modifications'])
    def test_recheck_health_and_icon(self):
        self.assertTrue(json.loads(self.request('/api/recheck',{})[2])['findings'])
        self.assertTrue(json.loads(self.request('/api/health')[2])['ok'])
        self.assertEqual(self.request('/favicon.ico')[0],204)
    def test_new_information_http(self):
        data=dict(category='cancellation',value='12',title='Exemple HTTP',excerpt='Annulation à 12 heures',source_url='https://example.org/demo',scope='regular',confirmed=True,simulated=True)
        code,_,body=self.request('/api/information',data);self.assertEqual(code,200)
        f=json.loads(body)['findings'][-1];self.assertEqual(f['status'],'Potential mismatch')
        data.update(id=f['id'],value='48');code,_,body=self.request('/api/information',data)
        self.assertEqual(json.loads(body)['findings'][-1]['status'],'Compatible input')
    def test_french_empty_form_and_missing_field_errors(self):
        for path,data,expected in (('/api/snapshot',{},'Le texte local'),('/api/scenario',{},'Le formulaire est incomplet'),('/api/information',{},'Valeur numérique attendue')):
            code,_,body=self.request(path,data);self.assertEqual(code,400);self.assertIn(expected,json.loads(body)['error'])
    def test_french_invalid_json_and_unknown_page(self):
        request=urllib.request.Request(self.base+'/api/recheck',data=b'{broken')
        try:urllib.request.urlopen(request,timeout=5);self.fail('Invalid JSON accepted')
        except urllib.error.HTTPError as e:self.assertIn('Les données JSON sont illisibles',json.load(e)['error'])
        code,_,body=self.request('/page-absente');self.assertEqual(code,404);self.assertIn('introuvable',json.loads(body)['error'])
    def test_french_export_includes_employer(self):
        code,_,body=self.request('/api/export');self.assertEqual(code,200)
        data=json.loads(body);self.assertTrue(any('employeur' in f['titre'] for f in data['problemes']))
        self.assertNotIn('Clarity concern',body.decode())

if __name__=='__main__':unittest.main(verbosity=2)
