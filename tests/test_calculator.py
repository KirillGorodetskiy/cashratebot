import unittest

from calculator import convert_amount, format_conversion, parse_amount


class TestCalculator(unittest.TestCase):
    def test_convert_amount(self) -> None:
        result = convert_amount(1000, 92.5, 90.1)
        self.assertEqual(result['pay_rub'], 92500.0)
        self.assertEqual(result['get_rub'], 90100.0)

    def test_parse_valid_amount(self) -> None:
        self.assertEqual(parse_amount('1 000.5'), 1000.5)
        self.assertEqual(parse_amount('1000'), 1000.0)

    def test_parse_rejects_bad_amount(self) -> None:
        self.assertIsNone(parse_amount('abc'))
        self.assertIsNone(parse_amount('-5'))
        self.assertIsNone(parse_amount('0'))
        self.assertIsNone(parse_amount('10000000000'))

    def test_format_escapes_bank_name(self) -> None:
        text = format_conversion(
            100,
            'USD',
            'Bank <script>',
            {'pay_rub': 9250.0, 'get_rub': 9010.0},
            'en',
        )
        self.assertIn('Bank &lt;script&gt;', text)
        self.assertNotIn('<script>', text)


if __name__ == '__main__':
    unittest.main()
