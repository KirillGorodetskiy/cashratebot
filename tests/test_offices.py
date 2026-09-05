import unittest
from unittest.mock import patch

from rbc_parser import parse_quotes


OFFICE_HTML = """
<html><body>
<div class="quote__office__content js-office-content">
  <div class="quote__office__one js-one-office">
    <a href="/cash/bank/104060.html"
       class="quote__office__one__name">Test Bank</a>
    <div class="quote__office__one__phone">+7 495 000-00-00</div>
    <div class="quote__office__cell quote__office__one__rate quote__mode_list_view">
      92.50
    </div>
    <div class="quote__office__cell quote__office__one__time">14:32</div>
    <div class="quote__office__cell quote__office__one__metro">
      <span>Kievskaya</span>
      <span class="quote__office__metro__distance">200 m</span>
    </div>
  </div>
</div>
</body></html>
"""


class TestOfficeParse(unittest.TestCase):
    def test_parses_metro_phone_and_bank_id(self) -> None:
        class FakeResponse:
            text = OFFICE_HTML

            def raise_for_status(self) -> None:
                return None

        with patch(
            'rbc_parser.requests.get',
            return_value=FakeResponse(),
        ):
            data = parse_quotes(
                'https://example.test',
                'quote__office__content js-office-content',
                'usd',
            )
        self.assertEqual(data.banks_names, ['Test Bank'])
        self.assertEqual(data.bank_ids, ['104060'])
        self.assertEqual(data.metros, ['Kievskaya'])
        self.assertEqual(data.phones, ['+7 495 000-00-00'])
        self.assertEqual(data.quotes, [92.5])


if __name__ == '__main__':
    unittest.main()
