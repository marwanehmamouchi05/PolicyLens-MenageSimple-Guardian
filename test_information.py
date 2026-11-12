import json,tempfile,unittest
from pathlib import Path
from guardian import Guardian,report
class InformationTests(unittest.TestCase):
    def setUp(self):
        self.app=Guardian()
        self.data=dict(category='cancellation',value='12',title='Article fictif de démonstration',excerpt='Annulation gratuite jusqu’à 12 heures avant le ménage.',source_url='https://example.org/article-fictif',scope='regular',confirmed=True,simulated=True)
    def submit(self,**changes):return self.app.information(dict(self.data,**changes))
    def test_new_twelve_hour_mismatch_uses_engine(self):
        f=self.submit()['findings'][-1];self.assertEqual(f['status'],'Potential mismatch');self.assertEqual(f['check']['flag_count'],2)
    def test_changed_fortyeight_clears_same_input(self):
        a=self.submit()['findings'][-1];f=self.submit(id=a['id'],value='48',excerpt='Annulation gratuite jusqu’à 48 heures avant le ménage.')['findings'][-1]
        self.assertEqual(f['id'],a['id']);self.assertEqual(f['check']['flag_count'],0);self.assertEqual(f['status'],'Compatible input');self.assertEqual(len(self.app.view()['information_history']),2)
    def test_compatible_statement_never_conflicts(self):
        f=self.submit(value='48')['findings'][-1];self.assertEqual(f['status'],'Compatible input');self.assertEqual(f['check']['flags'],[])
    def test_varied_values_not_special_cased(self):
        for v in ('6','36','72','47.5'):
            self.assertEqual(self.submit(value=v)['findings'][-1]['status'],'Potential mismatch')
    def test_second_category_fee_percentage(self):
        self.assertEqual(self.submit(category='late_fee',value='50')['findings'][-1]['status'],'Potential mismatch')
        self.assertEqual(self.submit(category='late_fee',value='90')['findings'][-1]['status'],'Compatible input')
    def test_missing_conditions_or_wrong_scope_abstains(self):
        self.assertEqual(self.submit(confirmed=False)['findings'][-1]['status'],'Insufficient evidence')
        self.assertEqual(self.submit(scope='other')['findings'][-1]['status'],'Insufficient evidence')
    def test_url_is_not_verified_evidence(self):
        f=self.submit()['findings'][-1];self.assertEqual(f['check']['flags'][0]['kind'],'needs_context');self.assertIn('non vérifiée',f['alternatives'])
    def test_invalid_inputs_block(self):
        for d in (dict(value='NaN'),dict(value='-1'),dict(category='unknown'),dict(source_url='javascript:alert(1)'),dict(confirmed='yes')):
            with self.assertRaises(ValueError):self.submit(**d)
        self.assertEqual(len(self.app.view()['information']),0)
    def test_review_versioning_and_french_report(self):
        f=self.submit()['findings'][-1];self.app.review(dict(id=f['id'],fingerprint=f['fingerprint'],decision='Request clarification',wording='À confirmer',note='Démonstration'))
        out=report(self.app.view());self.assertIn('Synthèse pour le responsable',out);self.assertIn('Exemple fictif saisi',out);self.assertIn('URL non vérifiée',out);self.assertIn('Article fictif',out)
        f=self.submit(id=f['id'],value='48')['findings'][-1];self.assertIsNone(f['review'])
    def test_new_information_persists(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'state.json';a=Guardian(p);a.information(self.data)
            self.assertEqual(Guardian(p).view()['findings'][-1]['status'],'Potential mismatch')
    def test_old_state_migrates_without_data_loss(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'state.json';old=self.app.state.copy();old.pop('information');old.pop('information_history');p.write_text(json.dumps(old),encoding='utf-8')
            a=Guardian(p);self.assertEqual(len(a.view()['findings']),5);self.assertEqual(a.view()['history'],old['history'])

if __name__=='__main__':unittest.main(verbosity=2)
