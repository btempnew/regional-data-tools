import unittest
from pathlib import Path
import json
import os
import tempfile
from unittest.mock import patch

from continue_run import continuation
from strict_titles import strict_role
from task_pipeline import HERE, literal, plan, main


class MassiveRunTests(unittest.TestCase):
    def test_catalog_and_every_region_have_separate_tasks(self):
        roles = literal(HERE/'linkedin_68_roles.py', 'ROLES')
        self.assertEqual(len(roles), 79)
        self.assertNotIn('Buyer', roles)
        for role in roles + ['procurement', 'commodity', 'category', 'buyer', 'purchasing', 'Sourcing']:
            tasks = plan([role], 'states', mode='all', groups=51)
            self.assertEqual(len(tasks), 51)
            self.assertTrue(all(len(t['locations']) == 1 for t in tasks))
            self.assertEqual(len({t['id'] for t in tasks}), 51)
            self.assertIn('Wyoming, United States', [t['locations'][0] for t in tasks])

    def test_strict_titles_do_not_expand_removed_or_partial_roles(self):
        catalog = literal(HERE/'linkedin_68_roles.py', 'ROLES')
        self.assertEqual(strict_role(' senior   BUYER ', catalog), 'Senior Buyer')
        for title in ['Buyer', 'Buyer II', 'Senior Buyer - Remote', 'Procurement Manager / Buyer', 'Senior Buyer Intern']:
            self.assertEqual(strict_role(title, catalog), '')

    def test_continuation_keeps_inputs_and_points_to_latest_artifacts(self):
        progress = {'pending_regions': [{}], 'unique_postings_missing_descriptions': 2}
        result = continuation(progress, {'roles': 'Sourcing', 'post_time': 'month'}, 123)
        self.assertEqual(result['roles'], 'Sourcing')
        self.assertEqual(result['post_time'], 'month')
        self.assertEqual(result['resume_run_id'], '123')
        self.assertEqual(result['previous_remaining'], '3')

    def test_continuation_retries_progress_but_not_source_caps_forever(self):
        self.assertIsNone(continuation({'pending_regions': [], 'capped_regions': [{}]}, {}, 1))
        progress = {'pending_regions': [{}]}
        self.assertIsNone(continuation(progress, {'auto_continue': 'false'}, 1))
        self.assertIsNone(continuation(progress, {'previous_remaining': '1', 'previous_saved': '0', 'continuation_stalls': '2'}, 1))
        self.assertIsNone(continuation({**progress, 'pipeline_error': True}, {}, 1))
        self.assertEqual(continuation(progress, {'previous_remaining': '2', 'continuation_stalls': '2'}, 1)['continuation_stalls'], '0')
        self.assertEqual(continuation({**progress, 'unique_postings_saved': 20},
                                      {'previous_remaining': '1', 'previous_saved': '10', 'continuation_stalls': '2'}, 1)['continuation_stalls'], '0')

    def test_manifest_contains_expected_unstarted_regions(self):
        roles = plan(['Sourcing'], 'national')
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'ROLE_PLAN': json.dumps({'include': roles})}):
            target = Path(tmp)/'progress.json'
            with patch('sys.argv', ['task_pipeline', 'report', '--root', tmp, '--output', str(target)]):
                main()
            progress = json.loads(target.read_text())
        self.assertEqual(len(progress['pending_regions']), 51)
        self.assertFalse(progress['complete'])

    def run_report(self, states, mode='auto'):
        roles = plan(['Sourcing'], 'national')
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'ROLE_PLAN': json.dumps({'include': roles}), 'STATE_SPLIT_MODE': mode}):
            for index, state in enumerate(states):
                (Path(tmp)/f'{index}_state.json').write_text(json.dumps(state))
            target = Path(tmp)/'progress.json'
            with patch('sys.argv', ['task_pipeline', 'report', '--root', tmp, '--output', str(target)]):
                main()
            return json.loads(target.read_text())

    def national_state(self, **where):
        task = plan(['Sourcing'], 'national')[0]
        return {'task_id': task['id'], 'role': 'Sourcing', 'kind': 'national', 'expected_locations': task['locations'],
                'complete': where.get('done', False), 'capped': where.get('capped', False), 'locations': {'United States': where}}

    def test_auto_report_is_complete_when_the_nationwide_search_finished(self):
        progress = self.run_report([self.national_state(done=True, reason='observed_end', next_offset=30)])
        self.assertEqual(progress['pending_regions'], [])
        self.assertTrue(progress['complete'])

    def test_auto_report_expects_states_after_a_capped_nationwide_search(self):
        progress = self.run_report([self.national_state(done=True, capped=True, reason='cap', next_offset=1000)])
        self.assertEqual(len(progress['pending_regions']), 51)
        self.assertEqual(progress['capped_regions'], [])
        self.assertNotIn('United States', [item['location'] for item in progress['pending_regions']])

    def test_auto_report_expects_the_nationwide_search_before_it_runs(self):
        self.assertEqual(len(self.run_report([])['pending_regions']), 51)


if __name__ == '__main__':
    unittest.main()
