"""Regression checks for defects found in the independent integration audit."""
import json, unittest
from guardian import Guardian, SUGGESTION, report
from impact_graph import impact, simulate_claim_correction
from impact_integration import action, initial_data, state
from report_fr import export_data

def claim(ident='reviewer'):
    return dict(id=ident,topic='cancellation_hours',value='12',scope='regular',source_url='https://menagesimple.com/',evidence='Exemple fictif : délai de 12 heures.',observed='2026-11-12')

class ReleaseGuardrails(unittest.TestCase):
    def test_simulation_never_relabels_original_quote_as_verified(self):
        d=initial_data();before=next(c for c in d['claims'] if c['id']=='CAN-CGV')
        r=simulate_claim_correction(d,'CAN-CGV','72');after=next(c for c in r['data']['claims'] if c['id']=='CAN-CGV')
        self.assertEqual(after['evidence'],before['evidence']);self.assertEqual(after['recorded_value'],'48')
        self.assertTrue(after['simulation']);self.assertEqual(after['verification'],'user_supplied')
        self.assertEqual(next(c for c in d['claims'] if c['id']=='CAN-CGV')['value'],'48')
    def test_history_survives_view_and_report(self):
        a=Guardian();action(a,'add',{'claim':claim()});action(a,'simulate',{'claim_id':'reviewer','new_value':'48'})
        self.assertEqual([h['action'] for h in state(a)['history']],['add','simulate'])
        r=action(a,'report',{})['export_fr'];self.assertEqual(r['historique'][-1]['avant'],'12');self.assertEqual(r['historique'][-1]['apres'],'48')
    def test_policy_proposal_survives_reload_state_and_export(self):
        a=Guardian();action(a,'impact',{'topic':'cancellation_hours','proposed_value':'72'})
        self.assertEqual(state(a)['proposals']['cancellation_hours'],'72')
        r=action(a,'report',{})['export_fr']['politiques'][0]
        self.assertEqual(r['hypothese_simulee'],'72');self.assertTrue(any(x['statut']=='Écart potentiel' for x in r['references_indexees']))
    def test_reset_removes_history_and_proposal_without_crossing_users(self):
        a,b=Guardian(),Guardian();action(a,'add',{'claim':claim()});action(a,'impact',{'topic':'cancellation_hours','proposed_value':'72'})
        self.assertEqual(state(b)['history'],[]);self.assertEqual(state(b)['proposals'],{})
        action(a,'reset',{});self.assertEqual(state(a)['history'],[]);self.assertEqual(state(a)['proposals'],{})
    def test_same_employer_wording_still_requires_context(self):
        rows=impact(initial_data(),'employer_role')['rows']
        self.assertTrue(rows);self.assertTrue(all(x['status']=='a_verifier' for x in rows))
    def test_unknown_service_cannot_be_marked_aligned(self):
        d=initial_data();c=next(c for c in d['claims'] if c['id']=='CAN-CGV');c['scope']='other'
        self.assertEqual(next(r['status'] for r in impact(d,'cancellation_hours')['rows'] if r['claim_id']=='CAN-CGV'),'a_verifier')
    def test_manual_information_is_bounded(self):
        a=Guardian()
        for i in range(30):action(a,'add',{'claim':claim(str(i))})
        with self.assertRaisesRegex(ValueError,'30 informations'):action(a,'add',{'claim':claim('over-limit')})
    def test_manual_payload_cannot_claim_fresh_verification(self):
        c=claim();c['verification']='fresh_index';a=Guardian();d=action(a,'add',{'claim':c})
        self.assertEqual(next(x['verification'] for x in d['data']['claims'] if x['id']=='reviewer'),'user_supplied')
    def test_historical_source_date_is_the_saved_ninth_not_an_invented_fifth(self):
        c=next(c for c in initial_data()['claims'] if c['id']=='CAN-PRIX-HIST')
        self.assertEqual(c['observed'],'2026-11-09');self.assertEqual(c['evidence'],'sans frais si c’est fait 24h à l’avance.')
    def test_generic_delegation_does_not_assert_company_is_employer(self):
        c=next(c for c in initial_data()['claims'] if c['id']=='EMP-GUIDE-EN')
        self.assertEqual(c['value'],'gestion_administrative_deleguee')
    def test_old_unmatched_sources_are_not_fresh(self):
        d=initial_data()
        for cid in ['VAC-FULLY','VAC-ROLLE','PAY-ROLLE','PAY-FULLY']:
            self.assertEqual(next(c['verification'] for c in d['claims'] if c['id']==cid),'not_verified')
    def test_main_snapshot_is_visible_in_graph_without_changing_evidence(self):
        a=Guardian();a.change(dict(text=SUGGESTION,scope='regular',confirmed=True));c=next(c for c in state(a)['data']['claims'] if c['id']=='CAN-PRIX-HIST')
        self.assertEqual(c['value'],'48');self.assertTrue(c['simulation']);self.assertEqual(c['status'],'historical');self.assertIn('24h',c['evidence'])
    def test_main_structured_menagesimple_input_is_adapted_to_graph(self):
        a=Guardian();a.information(dict(category='cancellation',value='12',title='Exemple',excerpt='Exemple fictif de 12 h',source_url='https://menagesimple.com/',scope='regular',confirmed=True,simulated=True))
        self.assertTrue(any(c.get('origin')=='guardian' for c in state(a)['data']['claims']))
    def test_graph_correction_updates_the_imported_guardian_value(self):
        a=Guardian();a.information(dict(category='cancellation',value='12',title='Exemple',excerpt='Exemple fictif de 12 h',source_url='https://menagesimple.com/',scope='regular',confirmed=True,simulated=True))
        c=next(c for c in state(a)['data']['claims'] if c.get('origin')=='guardian')
        action(a,'simulate',dict(claim_id=c['id'],new_value='48'))
        self.assertEqual(a.state['information'][0]['value'],'48')
        self.assertEqual(next(x['value'] for x in state(a)['data']['claims'] if x['id']==c['id']),'48')
        self.assertEqual(a.view()['findings'][-1]['status'],'Compatible input')
    def test_historical_evidence_is_not_rewritten_from_the_graph(self):
        a=Guardian()
        with self.assertRaisesRegex(ValueError,'preuve historique'):action(a,'simulate',dict(claim_id='CAN-PRIX-HIST',new_value='48'))
        self.assertEqual(next(x['value'] for x in state(a)['data']['claims'] if x['id']=='CAN-PRIX-HIST'),'24')
    def test_french_exports_contain_actual_graph_values_and_history(self):
        a=Guardian();action(a,'add',{'claim':claim()});action(a,'simulate',{'claim_id':'reviewer','new_value':'48'})
        text=report(a.view());self.assertIn('Correction simulée',text);self.assertIn('Exemple fictif : délai de 12 heures.',text)
        data=export_data(a.view())['graphe_impact'];self.assertIn('politiques',data);self.assertIn('historique',data)
        raw=json.dumps(data,ensure_ascii=False)
        for internal in ['fresh_index','needs_context','source_url','client_employeur']:self.assertNotIn(internal,raw)

if __name__=='__main__':unittest.main()
