import unittest

from inline_search import parse_inline_query


class TestInlineParse(unittest.TestCase):
    def test_usdt_query(self) -> None:
        parsed = parse_inline_query('usdt')
        self.assertEqual(parsed['kind'], 'usdt')

    def test_city_currency(self) -> None:
        parsed = parse_inline_query('moscow usd')
        self.assertEqual(parsed['kind'], 'cash')
        self.assertEqual(parsed['city'], 'Moscow')
        self.assertEqual(parsed['currency'], 'USD')

    def test_russian_city(self) -> None:
        parsed = parse_inline_query('спб eur')
        self.assertEqual(parsed['city'], 'SPB')
        self.assertEqual(parsed['currency'], 'EUR')

    def test_empty_is_none(self) -> None:
        self.assertIsNone(parse_inline_query(''))
        self.assertIsNone(parse_inline_query('hello world'))


if __name__ == '__main__':
    unittest.main()
