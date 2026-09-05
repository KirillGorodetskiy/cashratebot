import unittest
from unittest.mock import patch

import pandas as pd
import requests

from cities import CITIES, button_label, city_keys
from models import CityCode
from bot_logic import get_city_code, get_quotes_df
from rbc_parser import parse_quotes
import ui


class TestCityCatalog(unittest.TestCase):
    def test_catalog_matches_rbc_ids(self) -> None:
        expected = {
            'Moscow': 1,
            'SPB': 2,
            'Rostov': 3,
            'Kaliningrad': 4,
            'Krasnodar': 5,
            'Bashkortostan': 6,
            'Tatarstan': 7,
            'Volgograd': 8,
        }
        actual = {city.key: city.rbc_id for city in CITIES}
        self.assertEqual(actual, expected)

    def test_city_code_enum_matches_catalog(self) -> None:
        for city in CITIES:
            self.assertEqual(
                get_city_code(city.key),
                city.rbc_id,
            )
            self.assertEqual(
                CityCode[city.key.upper()].value,
                city.rbc_id,
            )

    def test_unknown_city_code_raises(self) -> None:
        with self.assertRaises(ValueError):
            get_city_code('Hack')


class TestCitiesKeyboard(unittest.TestCase):
    def test_keyboard_lists_every_catalog_city(self) -> None:
        markup = ui.cities_inline_keyboard('en')
        data = [
            button.callback_data
            for row in markup.inline_keyboard
            for button in row
        ]
        for key in city_keys():
            self.assertIn(f'city:{key}', data)
        self.assertIn('nav:back', data)
        self.assertLessEqual(
            max(len(item) for item in data),
            64,
        )

    def test_parse_city_accepts_catalog_and_rejects_unknown(self) -> None:
        self.assertEqual(ui.parse_city('city:Tatarstan'), 'Tatarstan')
        self.assertIsNone(ui.parse_city('city:Hack'))

    def test_city_buttons_use_flags_and_short_names(self) -> None:
        moscow = next(city for city in CITIES if city.key == 'Moscow')
        spb = next(city for city in CITIES if city.key == 'SPB')
        self.assertTrue(button_label(moscow, 'en').startswith('🏙'))
        self.assertIn('SPb', button_label(spb, 'en'))
        self.assertEqual(CITIES[0].key, 'Moscow')
        self.assertEqual(CITIES[1].key, 'SPB')


class TestParseQuotesSkip(unittest.TestCase):
    def test_missing_container_returns_empty(self) -> None:
        html = '<html><body><div>no table</div></body></html>'

        class FakeResponse:
            text = html

            def raise_for_status(self) -> None:
                return None

        with patch(
            'rbc_parser.requests.get',
            return_value=FakeResponse(),
        ):
            data = parse_quotes('https://example.test', 'missing', 'usd')
        self.assertEqual(data.banks_names, [])
        self.assertEqual(data.quotes, [])

    def test_request_error_returns_empty(self) -> None:
        with patch(
            'rbc_parser.requests.get',
            side_effect=requests.ConnectionError('down'),
        ):
            data = parse_quotes('https://example.test', 'box', 'usd')
        self.assertEqual(data.banks_names, [])


class TestQuotesSkipOnFailure(unittest.TestCase):
    def test_get_quotes_df_returns_empty_on_parse_error(self) -> None:
        with (
            patch('bot_logic.redis_client.REDIS_AVAILABLE', False),
            patch(
                'bot_logic.parse_quotes',
                side_effect=RuntimeError('parse failed'),
            ),
        ):
            df = get_quotes_df('USD', 'Kaliningrad')
        self.assertTrue(df.empty)
        self.assertIsInstance(df, pd.DataFrame)

    def test_get_quotes_df_returns_empty_for_unknown_city(self) -> None:
        with patch('bot_logic.redis_client.REDIS_AVAILABLE', False):
            df = get_quotes_df('USD', 'Hack')
        self.assertTrue(df.empty)


if __name__ == '__main__':
    unittest.main()
