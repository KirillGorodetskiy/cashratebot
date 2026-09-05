import unittest

from bb_api import build_message


class TestBuildMessageHtml(unittest.TestCase):
    def test_empty_result(self) -> None:
        text = build_message(None, lang='en')
        self.assertIn('Not enough data', text)

    def test_html_and_escaped_source_name(self) -> None:
        result = {
            'rates': {'Coin<base>': 92.5},
            'average': 92.5,
            'median': 92.5,
            'min': 92.5,
            'max': 92.5,
            'count': 1,
            'total': 6,
        }
        text = build_message(result, lang='en')
        self.assertIn('<b>', text)
        self.assertIn('Coin&lt;base&gt;', text)
        self.assertNotIn('<base>', text)
        self.assertIn('92.50', text)


if __name__ == '__main__':
    unittest.main()
