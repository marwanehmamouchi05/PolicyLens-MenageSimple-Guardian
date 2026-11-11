import json,tempfile,unittest
from pathlib import Path
from guardian import Guardian,SOURCES,EXCERPTS,SUGGESTION,report
from report_fr import export_data

class EmployerTests(unittest.TestCase):
    def setUp(self):self.app=Guardian()
    def employer(self):return next(f for f in self.app.view()['findings'] if f['id']=='employer')
    def test_four_categories_and_context_status(self):
        self.assertEqual({f['id'] for f in self.app.view()['findings']},{'cancellation','employer','reference','equipment'})
        f=self.employer();self.assertEqual(f['status'],'Clarity concern');self.assertIn('clarification nécessaire',f['explanation'])
    def test_correct_sources_language_dates_scope(self):
        f=self.employer()
        self.assertEqual({EXCERPTS[q]['source'] for q in f['evidence']},{'english','faq','terms'})
        for q in f['evidence']:
            self.assertEqual(EXCERPTS[q]['observed'],'2026-11-10');self.assertFalse(EXCERPTS[q]['historical']);self.assertTrue(EXCERPTS[q]['url'].startswith('https://menagesimple.com/'))
        for source in SOURCES['sources']:self.assertIn(source['language'],('fr','en'));self.assertTrue(source['scope'])
    def test_generic_scope_not_verified_legal_conflict(self):
        f=self.employer();self.assertTrue(f['check']['flags'])
        self.assertTrue(all(x['kind']=='needs_context' for x in f['check']['flags']))
        self.assertEqual(f['claims'][0]['scope'],'generic-model');self.assertEqual(f['claims'][0]['value'],'not_specified_in_generic_guide')
    def test_employer_identity_distinct_from_admin(self):
        claims=self.employer()['claims'];self.assertEqual({c['topic'] for c in claims},{'employer_role','administrative_manager'})
        self.assertEqual(next(c['value'] for c in claims if c['id']=='terms-role'),'customer_is_legal_employer')
        self.assertEqual(len(self.employer()['context']),4)
    def test_approval_never_resolves_context_issue(self):
        f=self.employer();self.app.review(dict(id=f['id'],fingerprint=f['fingerprint'],decision='Accept',wording=f['suggestion'],note='Clarification demandée'))
        self.app.change(dict(text=SUGGESTION,scope='regular',confirmed=True))
        self.assertEqual(self.employer()['status'],'Clarity concern');self.assertEqual(self.employer()['review']['decision'],'Accept')
    def test_review_persists_locally(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'state.json';a=Guardian(p);f=next(f for f in a.view()['findings'] if f['id']=='employer')
            a.review(dict(id=f['id'],fingerprint=f['fingerprint'],decision='Request clarification',wording=f['suggestion'],note='Quel modèle ?'))
            f=next(f for f in Guardian(p).view()['findings'] if f['id']=='employer')
            self.assertEqual(f['review']['note'],'Quel modèle ?');self.assertEqual(f['status'],'Clarity concern')
    def test_french_report_and_original_quote(self):
        text=report(self.app.view());self.assertIn('Qui est réellement l’employeur ?',text);self.assertIn('With a company, everything is delegated.',text);self.assertIn('Une gestion déléguée',text);self.assertIn('2026-11-10',text)
    def test_french_json_does_not_export_internal_english_labels(self):
        data=export_data(self.app.view());raw=json.dumps(data,ensure_ascii=False)
        for token in ('Wording inconsistency','Clarity concern','customer_is_legal_employer','Potential mismatch','After owner confirmation'):self.assertNotIn(token,raw)
        self.assertEqual(len(data['problemes']),4)
    def test_historical_cancellation_is_not_current_conflict(self):
        self.assertTrue(EXCERPTS['pricing-notice']['historical']);self.assertIn('48h',EXCERPTS['pricing-current']['quote'])
        self.assertEqual(EXCERPTS['pricing-notice']['observed'],'2026-11-09');self.assertIn('historique',self.app.view()['findings'][0]['display']['status'])

if __name__=='__main__':unittest.main(verbosity=2)
