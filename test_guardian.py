import json, tempfile, unittest
from pathlib import Path
from guardian import Guardian, SUGGESTION, ORIGINAL, EXCERPTS, SOURCES, findings, scenario, report
from engine import analyze, cancellation_scenario, validate_claims

class WorkflowTests(unittest.TestCase):
    def setUp(self):self.app=Guardian()
    def change(self,text=SUGGESTION,confirmed=True,scope='regular'):
        return self.app.change(dict(text=text,confirmed=confirmed,scope=scope))
    def test_conflict_flagged(self):
        f=self.app.view()['findings'][0]
        self.assertEqual(f['status'],'Wording inconsistency');self.assertGreater(f['check']['comparison']['flag_count'],0)
    def test_valid_correction_clears_specific_conflict(self):
        v=self.change();self.assertEqual(v['findings'][0]['status'],'Resolved in simulation')
        self.assertEqual(v['findings'][0]['check']['comparison']['flag_count'],0)
        self.assertEqual(v['findings'][1]['status'],'Wording inconsistency')
        self.assertEqual(v['findings'][2]['status'],'Clarity concern')
    def test_new_mismatch_reappears(self):
        self.change();v=self.change(SUGGESTION.replace('48','72'))
        self.assertEqual(v['findings'][0]['status'],'Wording inconsistency')
        self.assertEqual(v['history'][1]['before_status'],'Resolved in simulation')
    def test_matching_without_context_confirmation_is_insufficient(self):
        self.assertEqual(self.change(confirmed=False)['findings'][0]['status'],'Insufficient evidence')
    def test_different_service_does_not_resolve(self):
        self.assertEqual(self.change(scope='other')['findings'][0]['status'],'Insufficient evidence')
    def test_arbitrary_or_contradictory_text_abstains(self):
        for text in ('48 hours','No free cancellation before 48 hours',SUGGESTION+' Except customers cancelling at 24 hours.'):
            self.assertEqual(self.change(text)['findings'][0]['status'],'Insufficient evidence')
    def test_source_evidence_is_immutable(self):
        before=json.dumps(SOURCES,ensure_ascii=False);self.change();self.change(ORIGINAL,False)
        self.assertEqual(before,json.dumps(SOURCES,ensure_ascii=False))
    def test_cross_reference_is_deterministic(self):
        self.assertEqual(self.app.view()['findings'][1]['status'],'Wording inconsistency')
        old=EXCERPTS['terms-reference']['quote']
        try:
            EXCERPTS['terms-reference']['quote']=old.replace('10d','10c')
            self.assertEqual(self.app.view()['findings'][1]['status'],'Resolved in simulation')
        finally:EXCERPTS['terms-reference']['quote']=old
    def test_equipment_not_automatic_contradiction(self):
        f=self.app.view()['findings'][2];self.assertEqual(f['status'],'Clarity concern');self.assertIn('End-of-tenancy',f['alternatives'])
    def test_review_all_decisions(self):
        for d in ('Accept','Edit','Reject','Request clarification'):
            f=self.app.view()['findings'][0]
            v=self.app.review(dict(id=f['id'],fingerprint=f['fingerprint'],decision=d,wording='Owner to confirm scope',note='demo'))
            self.assertEqual(v['findings'][0]['review']['decision'],d)
        self.assertEqual(len(v['reviews']),4)
    def test_changed_content_invalidates_current_approval(self):
        f=self.app.view()['findings'][0];data=dict(id=f['id'],fingerprint=f['fingerprint'],decision='Accept',wording=SUGGESTION)
        self.app.review(data);self.change()
        self.assertIsNone(self.app.view()['findings'][0]['review'])
        with self.assertRaises(ValueError):self.app.review(data)
        self.assertEqual(len(self.app.view()['reviews']),1)
    def test_report_includes_decisions_history_and_escape(self):
        self.change('<script>alert(1)</script>');f=self.app.view()['findings'][0]
        self.app.review(dict(id=f['id'],fingerprint=f['fingerprint'],decision='Request clarification',wording='<bad>',note='<unsafe>'))
        out=report(self.app.view())
        for s in ('&lt;script&gt;','Demander une précision','Révision 1','SHA-256','https://menagesimple.com/conditions-generales/'):
            self.assertIn(s.casefold(),out.casefold())
        self.assertNotIn('<script>',out)
    def test_local_state_persists(self):
        with tempfile.TemporaryDirectory() as t:
            a=Guardian(Path(t)/'state.json');a.change(dict(text=SUGGESTION,scope='regular',confirmed=True))
            self.assertEqual(Guardian(Path(t)/'state.json').view()['revision'],1)
    def test_bad_snapshot_rejected(self):
        for data in (dict(text='',scope='regular',confirmed=True),dict(text='x',scope='regular',confirmed='yes')):
            with self.assertRaises(ValueError):self.app.change(data)

class CalculatorAndReusedCoreTests(unittest.TestCase):
    def scenario(self,notice='36',threshold='48'):
        return scenario(dict(rate='43.90',duration='2',notice=notice,threshold=threshold))
    def test_exact_money_example(self):
        r=self.scenario();self.assertEqual((r['booking_chf'],r['difference_chf'],r['selected_rule_chf']),('87.80','79.02','79.02'))
    def test_selected_article_rule(self):self.assertEqual(self.scenario(threshold='24')['selected_rule_chf'],'0.00')
    def test_boundaries(self):
        self.assertEqual(self.scenario('48')['selected_rule_chf'],'0.00')
        self.assertEqual(self.scenario('24','24')['selected_rule_chf'],'0.00')
        self.assertEqual(self.scenario('23.99','24')['selected_rule_chf'],'79.02')
    def test_decimal_rounding(self):
        self.assertEqual(scenario(dict(rate='10.01',duration='1.5',notice='1',threshold='48'))['selected_rule_chf'],'13.51')
    def test_negative_and_nonfinite_rejected(self):
        for val in ('-1','NaN','Infinity'):
            with self.assertRaises(ValueError):scenario(dict(rate=val,duration='2',notice='36',threshold='48'))
    def test_source_inventory(self):
        self.assertEqual(len(SOURCES['sources']),5)
        for s in SOURCES['sources']:
            self.assertEqual(s['http_status'],200);self.assertEqual(len(s['sha256']),64);self.assertTrue(s['url'].startswith('https://menagesimple.com/'))
    def test_reused_core_validates_ids_and_https(self):
        from guardian import claim
        c=claim('one',24,'pricing-notice','regular')
        with self.assertRaises(ValueError):validate_claims([c,c])
        c['source_url']='http://example.org'
        with self.assertRaises(ValueError):validate_claims([c])
    def test_reused_core_skips_nonoverlapping_dates(self):
        from guardian import claim
        a=claim('a',24,'pricing-notice','regular');b=claim('b',48,'terms-notice','regular')
        a['effective_until']='2025-12-31';b['effective_from']='2026-01-01'
        self.assertEqual(analyze([a,b])['flag_count'],0)

if __name__=='__main__':unittest.main(verbosity=2)
