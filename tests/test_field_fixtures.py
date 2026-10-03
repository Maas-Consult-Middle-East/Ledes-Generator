"""Check that a fresh install provides every canonical export custom field."""
import ast
import json
import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1] / 'ledes'


class TestFieldFixtures(unittest.TestCase):
    def test_export_fields_are_packaged(self):
        fields = json.loads((ROOT / 'fixtures/custom_field.json').read_text())
        packaged = {field['fieldname'] for field in fields}
        tree = ast.parse((ROOT / 'api/ledes.py').read_text())
        referenced = {
            node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
            and node.value.startswith('custom_')
        }
        legacy_aliases = {
            'custom_ledes_billing_start_date', 'custom_ledes_billing_end_date',
            'custom_line_item_date', 'custom_expense_code', 'custom_exp_fee_inv_adj_type',
        }
        self.assertEqual(referenced - legacy_aliases, packaged)
        names = [field['name'] for field in fields]
        self.assertEqual(len(names), len(set(names)))
        for field in fields:
            self.assertEqual(field['name'], f"{field['dt']}-{field['fieldname']}")
            self.assertEqual(field['module'], 'Ledes')
            if field['insert_after'].startswith('custom_'):
                self.assertIn(f"{field['dt']}-{field['insert_after']}", names)

    def test_install_hooks_and_settings_are_packaged(self):
        hooks = runpy.run_path(str(ROOT / 'hooks.py'))
        self.assertIn('erpnext', hooks['required_apps'])
        self.assertIn({'dt': 'Custom Field', 'filters': [['module', '=', 'Ledes']]}, hooks['fixtures'])
        settings = json.loads((ROOT / 'ledes/doctype/ledes_settings/ledes_settings.json').read_text())
        self.assertEqual(settings['issingle'], 1)
        self.assertEqual(set(settings['field_order']), {
            'default_invoice_description', 'vat_expense_code', 'vat_description',
        })
