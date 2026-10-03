"""Standalone export regression tests: python3 -m unittest discover -s tests."""
import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


class Doc(dict):
    def __getattr__(self, name):
        return self[name]


class TestExport(unittest.TestCase):
    def setUp(self):
        self.item = Doc(doctype='Sales Invoice Item', item_code='SERVICE',
                        description='Legal work', amount=200, rate=100, qty=2,
                        custom_ledes_adjustment_amount=15, custom_ledes_type='IF')
        self.doc = Doc(doctype='Sales Invoice', name='INV-1', owner='lawyer@example.com',
                       customer='CLIENT', company='FIRM', posting_date='20261003',
                       grand_total=230, total_taxes_and_charges=30, items=[self.item],
                       custom_your_financial_ref='MATTER-C', custom_our_reference='MATTER-F')
        self.settings = Doc(default_invoice_description='Configured description',
                            vat_expense_code='E999', vat_description='Configured tax')
        self.values = {
            ('Customer', 'CLIENT', 'custom_ledes_client_id'): 'CLIENT-42',
            ('Company', 'FIRM', 'custom_ledes_law_firm_id'): 'FIRM-24',
            ('Employee', 'EMP', 'custom_timekeeper_id'): 'TK-1',
            ('Employee', 'EMP', 'custom_timekeeper_classification'): 'PT',
            ('User', self.doc.owner, 'full_name'): 'Test Lawyer',
            ('Item', 'SERVICE', 'custom_task_code'): 'L100',
            ('Item', 'SERVICE', 'custom_activity_code'): 'A102',
        }

        def get_value(dt, name, field):
            if isinstance(name, dict):
                return 'EMP'
            return self.values.get((dt, name, field))

        def throw(message):
            raise ValueError(message)

        fake = SimpleNamespace(
            whitelist=lambda: lambda fn: fn, get_doc=lambda *args: self.doc,
            get_single=lambda name: self.settings,
            form_dict={'sales_invoice': 'INV-1'}, response={}, throw=throw,
            db=SimpleNamespace(get_value=get_value),
            get_meta=lambda dt: SimpleNamespace(has_field=lambda field: True),
            utils=SimpleNamespace(flt=lambda value: float(value or 0),
                                  formatdate=lambda value, fmt: value,
                                  strip_html=lambda value: value),
        )
        spec = importlib.util.spec_from_file_location(
            'ledes_export_under_test', Path(__file__).parents[1] / 'ledes/api/ledes.py')
        self.module = importlib.util.module_from_spec(spec)
        with patch.dict('sys.modules', {'frappe': fake}):
            spec.loader.exec_module(self.module)

    def export(self):
        text = self.module.generate_ledes_sales_invoice_txt('INV-1')['content']
        rows = [line.removesuffix('[]').split('|') for line in text.splitlines()[1:]]
        return [dict(zip(rows[0], row)) for row in rows[1:]]

    def test_configured_values_and_adjustments(self):
        regular, vat = self.export()
        for row in (regular, vat):
            self.assertEqual(row['CLIENT_ID'], 'CLIENT-42')
            self.assertEqual(row['LAW_FIRM_ID'], 'FIRM-24')
            self.assertEqual(row['TIMEKEEPER_CLASSIFICATION'], 'PT')
            self.assertEqual(row['CLIENT_MATTER_ID'], 'MATTER-C')
            self.assertEqual(row['LAW_FIRM_MATTER_ID'], 'MATTER-F')
            self.assertEqual(row['INVOICE_DESCRIPTION'], 'Configured description')
        self.assertEqual(regular['EXP/FEE/INV_ADJ_TYPE'], 'IF')
        self.assertEqual(regular['LINE_ITEM_ADJUSTMENT_AMOUNT'], '15.00')
        self.assertEqual(vat['LINE_ITEM_EXPENSE_CODE'], 'E999')
        self.assertEqual(vat['LINE_ITEM_DESCRIPTION'], 'Configured tax')
        self.assertEqual(vat['LINE_ITEM_TOTAL'], '30.00')

    def test_missing_master_configuration_blocks_export(self):
        for key, label in [
            (('Customer', 'CLIENT', 'custom_ledes_client_id'), 'LEDES Client ID'),
            (('Company', 'FIRM', 'custom_ledes_law_firm_id'), 'LEDES Law Firm ID'),
            (('Employee', 'EMP', 'custom_timekeeper_classification'), 'Timekeeper Classification'),
        ]:
            with self.subTest(field=label):
                value = self.values.pop(key)
                with self.assertRaisesRegex(ValueError, label):
                    self.export()
                self.values[key] = value

    def test_missing_matter_and_task_do_not_emit_placeholders(self):
        self.doc['custom_your_financial_ref'] = ''
        with self.assertRaisesRegex(ValueError, 'Your Financial Ref'):
            self.export()
        self.doc['custom_your_financial_ref'] = 'MATTER-C'
        self.values.pop(('Item', 'SERVICE', 'custom_task_code'))
        with self.assertRaisesRegex(ValueError, 'Task Code'):
            self.export()

    def test_expense_can_have_blank_task_and_activity(self):
        self.values.pop(('Item', 'SERVICE', 'custom_task_code'))
        self.values.pop(('Item', 'SERVICE', 'custom_activity_code'))
        self.item['custom_ledes_type'] = ''
        self.item['custom_ledes_expense_code'] = 'E101'
        row = self.export()[0]
        self.assertEqual(row['EXP/FEE/INV_ADJ_TYPE'], 'E')
        self.assertEqual(row['LINE_ITEM_TASK_CODE'], '')
        self.assertEqual(row['LINE_ITEM_ACTIVITY_CODE'], '')

    def test_invoice_description_overrides_default(self):
        self.doc['custom_ledes_invoice_description'] = 'Invoice specific'
        self.assertEqual(self.export()[0]['INVOICE_DESCRIPTION'], 'Invoice specific')


if __name__ == '__main__':
    unittest.main()
