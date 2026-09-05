import unittest

from bot_logic import get_currency_code
from currencies import CURRENCIES, currency_keys, get_rbc_id


class TestCurrencyCatalog(unittest.TestCase):
    def test_required_cash_currencies_exist(self) -> None:
        keys = currency_keys()
        for code in ('USD', 'EUR', 'GBP', 'AED', 'CNY', 'CHF', 'TRY'):
            self.assertIn(code, keys)

    def test_rbc_ids_for_new_currencies(self) -> None:
        self.assertEqual(get_rbc_id('CNY'), 423)
        self.assertEqual(get_rbc_id('CHF'), 305)
        self.assertEqual(get_rbc_id('TRY'), 307)
        self.assertEqual(get_rbc_id('USD'), 3)
        self.assertEqual(get_currency_code('CNY'), 423)
        self.assertEqual(get_currency_code('TRY'), 307)

    def test_unknown_currency_raises(self) -> None:
        with self.assertRaises(ValueError):
            get_rbc_id('XXX')

    def test_catalog_ids_are_unique(self) -> None:
        ids = [item.rbc_id for item in CURRENCIES]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == '__main__':
    unittest.main()
