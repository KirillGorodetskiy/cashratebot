import datetime
import unittest

import pandas as pd
import pytz

from data_formatter import (
    card_header,
    format_dataframe,
    format_stats_for_telegram,
)


MSK = pytz.timezone('Europe/Moscow')


def sample_quotes_df() -> pd.DataFrame:
    return pd.DataFrame({
        'bank': ['Sber <script>', 'VTB'],
        'buy_quote': [92.5, 93.1],
        'sell_quote': [90.1, 91.0],
        'avg_price': [91.3, 92.05],
        'spread': [2.4, 2.1],
        'spread_percent': [2.66, 2.31],
        'time': [
            MSK.localize(datetime.datetime(2026, 1, 1, 14, 32)),
            MSK.localize(datetime.datetime(2026, 1, 1, 14, 10)),
        ],
        'commissions': [False, True],
    })


class TestCardHeader(unittest.TestCase):
    def test_breadcrumb_and_updated_time(self) -> None:
        when = MSK.localize(datetime.datetime(2026, 1, 1, 20, 4))
        text = card_header(
            ['Cash', 'Moscow', 'USD'],
            'en',
            when,
        )
        self.assertIn('<b>Cash · Moscow · USD</b>', text)
        self.assertIn('Updated 20:04 MSK', text)


class TestFormatDataframeHtml(unittest.TestCase):
    def test_empty_dataframe_returns_empty_string(self) -> None:
        df = pd.DataFrame()
        self.assertEqual(format_dataframe(df, 'en'), '')

    def test_table_ranks_and_escapes_bank_name(self) -> None:
        text = format_dataframe(sample_quotes_df(), 'en')
        self.assertIn('<pre>', text)
        self.assertIn('★1', text)
        self.assertIn(' 2', text)
        self.assertIn('Sber &lt;script&gt;', text)
        self.assertNotIn('<script>', text)
        self.assertIn('92.50', text)
        self.assertIn('<blockquote expandable>', text)
        self.assertIn('14:32', text)
        self.assertIn('Commission: No', text)

    def test_russian_labels(self) -> None:
        text = format_dataframe(sample_quotes_df(), 'ru')
        self.assertIn('Комиссия: Нет', text)
        self.assertIn('Комиссия: Да', text)


class TestFormatStatsHtml(unittest.TestCase):
    def test_uses_pre_and_escapes_currency(self) -> None:
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
        self.assertIn('<pre>', text)
        self.assertIn('US&lt;D&gt;', text)
        self.assertNotIn('<d>', text)
        self.assertIn('<blockquote expandable>', text)


if __name__ == '__main__':
    unittest.main()
