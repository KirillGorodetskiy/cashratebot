import unittest
from unittest.mock import patch

from cbr_rates import parse_cbr_xml, format_cbr_line


SAMPLE_XML = """
<ValCurs>
  <Valute>
    <CharCode>USD</CharCode>
    <Nominal>1</Nominal>
    <Value>91,2000</Value>
  </Valute>
  <Valute>
    <CharCode>JPY</CharCode>
    <Nominal>100</Nominal>
    <Value>61,0000</Value>
  </Valute>
</ValCurs>
"""


class TestCbrParse(unittest.TestCase):
    def test_parses_rate_per_unit(self) -> None:
        rates = parse_cbr_xml(SAMPLE_XML)
        self.assertAlmostEqual(rates['USD'], 91.2)
        self.assertAlmostEqual(rates['JPY'], 0.61)

    def test_cbr_line_shows_premium(self) -> None:
        text = format_cbr_line('en', 91.2, 92.5)
        self.assertIn('91.20', text)
        self.assertIn('92.50', text)
        self.assertIn('+1.43%', text)

    def test_missing_cbr_returns_empty(self) -> None:
        with patch('cbr_rates.fetch_cbr_rates', return_value={}):
            from cbr_rates import cbr_compare_line
            self.assertEqual(cbr_compare_line('USD', 92.5, 'en'), '')


if __name__ == '__main__':
    unittest.main()
