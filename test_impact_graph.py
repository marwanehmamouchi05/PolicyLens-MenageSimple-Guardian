"""Regression suite: never confuses a structured-claim demo with a live crawler."""
import copy
import json
import unittest
from pathlib import Path

from impact_graph import (
    add_claim, build_graph, findings, impact, simulate_claim_correction,
    validate_claim, validate_dataset,
)
from impact_integration import BASE

def report_for(data):
    graph=build_graph(data)
    return {"limitation":"Analyse structurée, pas un scan complet.","indexed_claims":data["claims"],"graph_summary":graph["summary"],"findings":findings(data)}


def sample_claim(ident='SYN-NEW', topic='cancellation_hours', value='12', **kwargs):
    return {
        'id': ident, 'topic': topic, 'value': value, 'scope': 'regular',
        'source_url': f'https://menagesimple.com/test-{ident.lower()}/',
        'evidence': 'Cas synthétique pour une vérification de cohérence, pas un relevé du site.',
        'observed': '2026-11-11', 'verification': 'user_supplied',
        'service_model': 'menagesimple', **kwargs,
    }


class PolicyGraphTests(unittest.TestCase):
    def setUp(self):
        self.data = copy.deepcopy(BASE)

    def test_data_can_be_validated(self):
        self.assertEqual(len(validate_dataset(self.data)['claims']), 17)

    def test_current_cancellation_claims_agree(self):
        pairs = [f for f in findings(self.data) if f['topic'] == 'cancellation_hours']
        self.assertEqual(pairs, [])

    def test_historical_24h_not_treated_as_current(self):
        data = impact(self.data, 'cancellation_hours')
        statuses = {r['claim_id']:r['status'] for r in data['rows']}
        self.assertEqual(statuses['CAN-PRIX-HIST'], 'historique')
        for ident in ('CAN-CGV','CAN-FAQ','CAN-PRIX'):
            self.assertEqual(statuses[ident], 'conforme')

    def test_wrong_clause_reference_present(self):
        f = [f for f in findings(self.data) if f['kind'] == 'reference_mismatch']
        self.assertEqual(len(f), 1)
        self.assertEqual((f[0]['source_clause'],f[0]['target_clause']),('7','10d'))
        self.assertIn('10c', f[0]['expected_target_candidates'])

    def test_wrong_clause_appears_in_impact(self):
        refs = impact(self.data, 'cancellation_hours')['contract_references']
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]['status'], 'reference_incorrecte')

    def test_contract_reference_fixed_deterministically(self):
        self.data['references'][0]['target_clause'] = '10c'
        self.assertFalse(any(f['kind']=='reference_mismatch' for f in findings(self.data)))
        self.assertEqual(impact(self.data,'cancellation_hours')['contract_references'][0]['status'],'conforme')

    def test_graph_has_policy_page_claim_clause_edges(self):
        graph = build_graph(self.data)
        types = {n['type'] for n in graph['nodes']}
        self.assertEqual(types, {'policy','page','claim','clause'})
        edge_types = {edge['type'] for edge in graph['edges']}
        self.assertEqual(edge_types,{'contient','concerne','renvoi_contractuel','reference_a_verifier'})
        self.assertEqual(graph['summary']['indexed_pages'],7)

    def test_change_policy_affects_all_indexed_references(self):
        data = impact(self.data,'cancellation_hours',72)
        self.assertEqual(len(data['rows']),4)
        self.assertEqual(sum(r['status']=='ecart_potentiel' for r in data['rows']),3)
        self.assertEqual(data['contract_references'][0]['status'],'reference_incorrecte')
        self.assertTrue(all(c['value']!='72' for c in self.data['claims']))

    def test_add_unseen_synthetic_conflict_automatically(self):
        amended = add_claim(self.data,sample_claim())
        conflicts = [f for f in findings(amended) if 'SYN-NEW' in f.get('claim_ids',[])]
        self.assertGreaterEqual(len(conflicts),2)
        self.assertTrue(all(f['source_recheck_required'] for f in conflicts))
        self.assertEqual(len(self.data['claims']),17)

    def test_identical_new_value_not_flagged(self):
        amended = add_claim(self.data,sample_claim(value='48'))
        self.assertFalse(any('SYN-NEW' in f.get('claim_ids',[]) for f in findings(amended)))

    def test_correction_simulation_removes_conflicts_not_source(self):
        amended = add_claim(self.data,sample_claim())
        before = len(findings(amended))
        result=simulate_claim_correction(amended,'SYN-NEW','48')
        self.assertLess(result['new_count'],before)
        self.assertTrue(result['resolved_ids'])
        self.assertEqual(next(c['value'] for c in amended['claims'] if c['id']=='SYN-NEW'),'12')
        self.assertTrue(result['simulation_only'])

    def test_employer_role_requires_human_context(self):
        f=[x for x in findings(self.data) if x['topic']=='employer_role']
        self.assertGreaterEqual(len(f),1)
        self.assertTrue(all(x['kind']=='needs_context' for x in f))
        self.assertTrue(all(x['human_review_required'] for x in f))

    def test_older_index_requires_live_recheck(self):
        rows=impact(self.data,'equipment_vacuum')['rows']
        self.assertEqual(next(x['status'] for x in rows if x['claim_id']=='VAC-FULLY'),'a_verifier')

    def test_payment_difference_is_not_auto_legal_conflict(self):
        f=[x for x in findings(self.data) if x['topic']=='payment_arrangement']
        self.assertTrue(f)
        self.assertTrue(all(x['kind']=='needs_context' for x in f))

    def test_invalid_numerical_claim(self):
        with self.assertRaises(ValueError): validate_claim(sample_claim(value='abc'))
        with self.assertRaises(ValueError): validate_claim(sample_claim(value='0'))

    def test_external_sources_denied_in_demo(self):
        for url in ['http://menagesimple.com/test','https://evil.example/page',
                    'https://menagesimple.com.evil.example/','https://x:y@menagesimple.com/']:
            c=sample_claim()
            c['source_url']=url
            with self.subTest(url=url), self.assertRaises(ValueError): validate_claim(c)

    def test_duplicate_claim_ids_rejected(self):
        self.data['claims'].append(copy.deepcopy(self.data['claims'][0]))
        with self.assertRaises(ValueError): validate_dataset(self.data)

    def test_invalid_topic_rejected(self):
        with self.assertRaises(ValueError): validate_claim(sample_claim(topic='unrestricted_semantic_detection'))

    def test_unsupported_verification_rejected(self):
        with self.assertRaises(ValueError): validate_claim(sample_claim(verification='verified_without_check'))

    def test_report_contains_limitations_and_evidence(self):
        r=report_for(self.data)
        self.assertIn('pas un scan complet',r['limitation'])
        self.assertEqual(len(r['indexed_claims']),17)
        self.assertEqual(r['graph_summary']['review_items'],len(r['findings']))


if __name__ == '__main__':
    unittest.main()
