import datetime
import unittest

import pandas as pd

from data_formatter import format_dataframe, format_stats_for_telegram


def sample_quotes_df() -> pd.DataFrame:
    return pd.DataFrame({
        'bank': ['Sber <script>'],
        'buy_quote': [92.5],
        'sell_quote': [90.1],
        'avg_price': [91.3],
        'spread': [2.4],
        'spread_percent': [2.66],
        'time': [datetime.datetime(2026, 1, 1, 14, 32)],
        'commissions': [False],
    })


class TestFormatDataframeHtml(unittest.TestCase):
    def test_empty_dataframe_returns_empty_string(self) -> None:
        df = pd.DataFrame()
        self.assertEqual(format_dataframe(df, 'en'), '')

    def test_uses_html_and_escapes_bank_name(self) -> None:
        text = format_dataframe(sample_quotes_df(), 'en')
        self.assertIn('<b>', text)
        self.assertIn('Sber &lt;script&gt;', text)
        self.assertNotIn('<script>', text)
        self.assertIn('92.5', text)
        self.assertIn('14:32', text)

    def test_russian_labels(self) -> None:
        text = format_dataframe(sample_quotes_df(), 'ru')
        self.assertIn('Покупка', text)
        self.assertIn('Нет', text)


class TestFormatStatsHtml(unittest.TestCase):
    def test_uses_html_and_escapes_currency(self) -> None:
        stats = {
            'us<d>': {
                'avg_buys': 92.5,
                'avg_sells': 90.1,
                'avg_price': 91.3,
                'avg_spread_rub': 2.4,
                'min_spread_rub': 1.1,
                'max_spread_rub': 3.3,
                'num_of_available_buys': 4,
                'num_of_available_sells': 5,
            }
        }
        text = format_stats_for_telegram(stats, 'en')
        self.assertIn('<b>', text)
        self.assertIn('US&lt;D&gt;', text)
        self.assertNotIn('<d>', text)


if __name__ == '__main__':
    unittest.main()
