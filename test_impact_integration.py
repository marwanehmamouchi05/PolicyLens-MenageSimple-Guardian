"""Integration tests: graph lives inside Guardian, never affects other visitors."""
import unittest, json, threading, urllib.request, http.cookiejar, os
from unittest.mock import patch
from guardian import Guardian
from impact_integration import action,initial_data
from impact_graph import findings
import public_server as pub, server

class GraphIntegrationTests(unittest.TestCase):
    def test_graph_starts_from_attributed_claims(self):
        g=action(Guardian(),'state',{})
        self.assertEqual(len(g['data']['claims']),17)
        self.assertEqual(g['graph']['summary']['indexed_pages'],7)
        self.assertIn('verification',g['data']['claims'][0])
    def test_add_and_recheck_then_reset(self):
        app=Guardian();sample={'id':'SYN-TEST','topic':'cancellation_hours','value':'12','scope':'regular','source_url':'https://menagesimple.com/','evidence':'Cas fictif : délai de 12 h','observed':'2026-11-11','verification':'fresh_index'}
        out=action(app,'add',{'claim':sample});self.assertEqual(next(x for x in out['data']['claims'] if x['id']=='SYN-TEST')['verification'],'user_supplied')
        self.assertTrue(any('SYN-TEST' in x.get('claim_ids',[]) for x in out['graph']['findings']))
        correction=action(app,'simulate',{'claim_id':'SYN-TEST','new_value':'48'})
        self.assertTrue(correction['resolved_ids']);self.assertFalse(any('SYN-TEST' in x.get('claim_ids',[]) for x in correction['graph']['findings']))
        self.assertEqual(next(x for x in initial_data()['claims'] if x['id']=='CAN-CGV')['value'],'48')
        self.assertFalse(any(c['id']=='SYN-TEST' for c in action(app,'reset',{})['data']['claims']))
    def test_compatible_input_does_not_generate_conflict(self):
        a=Guardian();base=action(a,'state',{})['graph']['summary']['review_items'];sample={'id':'SYN-SAFE','topic':'cancellation_hours','value':'48','scope':'regular','source_url':'https://menagesimple.com/','evidence':'Cas fictif : délai de 48 h','observed':'2026-11-11'}
        r=action(a,'add',{'claim':sample});self.assertEqual(r['graph']['summary']['review_items'],base)
    def test_invalid_url_and_external_code_rejected(self):
        a=Guardian();c={'id':'bad','topic':'cancellation_hours','value':'12','scope':'regular','source_url':'https://evil.com/','evidence':'<script>alert(1)</script>','observed':'2026-11-11'}
        with self.assertRaises(ValueError): action(a,'add',{'claim':c})
    def test_users_not_shared(self):
        a,b=Guardian(),Guardian();c={'id':'only-a','topic':'cancellation_hours','value':'12','scope':'regular','source_url':'https://menagesimple.com/','evidence':'Fictif','observed':'2026-11-11'}
        action(a,'add',{'claim':c});self.assertEqual(len(action(a,'state',{})['data']['claims']),18);self.assertEqual(len(action(b,'state',{})['data']['claims']),17)
    def test_report_has_limitations(self):
        r=action(Guardian(),'report',{});self.assertIn('coverage',r);self.assertIn('findings',r);self.assertIn('human_review',r)

class GraphHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch=patch.dict(os.environ,LOCAL_PUBLIC_TEST='1');cls.patch.start()
        cls.prev=server.APP;server.APP=pub.SessionProxy();pub._sessions.clear();pub._rates.clear()
        cls.http=pub.PublicServer(('127.0.0.1',0),pub.Handler)
        cls.base=f'http://127.0.0.1:{cls.http.server_port}'
        cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown();cls.http.server_close();cls.thread.join();server.APP=cls.prev;cls.patch.stop()
    def client(self):return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def get(self,c,path):return c.open(self.base+path,timeout=5)
    def post(self,c,path,body):return c.open(urllib.request.Request(self.base+path,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'}),timeout=5)
    def test_http_flow_and_sessions(self):
        a,b=self.client(),self.client()
        self.assertIn(b'impact',self.get(a,'/impact.js').read())
        orig=json.load(self.get(a,'/impact/api/state'));self.assertEqual(len(orig['data']['claims']),17)
        claim={'id':'SYN-HTTP','topic':'cancellation_hours','value':'12','scope':'regular','source_url':'https://menagesimple.com/','evidence':'Fictif','observed':'2026-11-11'}
        after=json.load(self.post(a,'/impact/api/add',{'claim':claim}));self.assertEqual(len(after['data']['claims']),18)
        self.assertEqual(len(json.load(self.get(b,'/impact/api/state'))['data']['claims']),17)
        corrected=json.load(self.post(a,'/impact/api/simulate',{'claim_id':'SYN-HTTP','new_value':'48'}));self.assertTrue(corrected['resolved_ids'])
        self.assertIn('findings',json.load(self.post(a,'/impact/api/report',{})))
        self.assertEqual(len(json.load(self.post(a,'/impact/api/reset',{}))['data']['claims']),17)
