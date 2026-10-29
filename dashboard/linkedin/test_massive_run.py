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
        self.assertIsNone(continuation(progress, {'previous_remaining': '1', 'continuation_stalls': '2'}, 1))
        self.assertIsNone(continuation({**progress, 'pipeline_error': True}, {}, 1))
        self.assertEqual(continuation(progress, {'previous_remaining': '2', 'continuation_stalls': '2'}, 1)['continuation_stalls'], '0')

    def test_manifest_contains_expected_unstarted_regions(self):
        roles = plan(['Sourcing'], 'national')
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'ROLE_PLAN': json.dumps({'include': roles})}):
            target = Path(tmp)/'progress.json'
            with patch('sys.argv', ['task_pipeline', 'report', '--root', tmp, '--output', str(target)]):
                main()
            progress = json.loads(target.read_text())
        self.assertEqual(len(progress['pending_regions']), 51)
        self.assertFalse(progress['complete'])


if __name__ == '__main__':
    unittest.main()
