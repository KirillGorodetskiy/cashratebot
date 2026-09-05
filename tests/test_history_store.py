import unittest

from history_store import sparkline, summarize_history


class TestHistorySpark(unittest.TestCase):
    def test_sparkline_uses_blocks(self) -> None:
        line = sparkline([1, 2, 3, 4, 5, 6, 7, 8])
        self.assertTrue(set(line) <= set('▁▂▃▄▅▆▇█'))
        self.assertGreaterEqual(len(line), 4)

    def test_empty_history_is_empty(self) -> None:
        self.assertEqual(sparkline([]), '')
        self.assertEqual(summarize_history([], 'en'), '')

    def test_summary_has_min_max(self) -> None:
        points = [
            {'t': 1, 'buy': 90.0},
            {'t': 2, 'buy': 93.0},
            {'t': 3, 'buy': 91.5},
        ]
        text = summarize_history(points, 'en')
        self.assertIn('90.00', text)
        self.assertIn('93.00', text)


if __name__ == '__main__':
    unittest.main()
