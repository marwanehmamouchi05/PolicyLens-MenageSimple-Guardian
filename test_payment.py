import json,tempfile,unittest
from pathlib import Path
from guardian import Guardian,report
from report_fr import export_data

class PaymentTests(unittest.TestCase):
    def payment(self,a):return next(f for f in a.view()['findings'] if f['id']=='payment')
    def test_shared_graph_evidence_and_prudent_status(self):
        a=Guardian();f=self.payment(a)
        self.assertEqual(f['proofs'],[c for c in a.view()['impact']['data']['claims'] if c['topic']=='payment_arrangement'])
        self.assertEqual(f['status'],'Insufficient evidence')
        self.assertEqual([c['verification'] for c in f['proofs']],['fresh_index','not_verified','not_verified'])
    def test_review_persists_without_confirming_old_quotes(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'state.json';a=Guardian(p);f=self.payment(a)
            a.review(dict(id=f['id'],fingerprint=f['fingerprint'],decision='Request clarification',wording=f['suggestion'],note='Confirmer garantie et règlement.'))
            f=self.payment(Guardian(p));self.assertEqual(f['status'],'Insufficient evidence');self.assertEqual(f['review']['decision'],'Request clarification')
    def test_report_qualifies_current_and_unverified_evidence(self):
        a=Guardian();f=next(p for p in export_data(a.view())['problemes'] if p['titre']=='Carte, virement ou espèces ?')
        self.assertEqual(len(f['preuves']),3)
        self.assertEqual([p['presence_actuelle_verifiee'] for p in f['preuves']],[True,False,False])
        text=report(a.view());self.assertIn('Ancien extrait non authentifié',text);self.assertIn('Carte, virement ou espèces ?',text)
    def test_review_versions_if_evidence_is_requalified(self):
        a=Guardian();before=self.payment(a)['fingerprint'];next(c for c in a.impact_data['claims'] if c['id']=='PAY-ROLLE')['verification_note']='Nouvelle lecture à confirmer.'
        self.assertNotEqual(before,self.payment(a)['fingerprint'])

if __name__=='__main__':unittest.main()
