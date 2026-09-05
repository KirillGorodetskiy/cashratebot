import unittest

from telegram import InlineKeyboardButton

import ui


class TestResolveLang(unittest.TestCase):
    def test_russian_prefix(self) -> None:
        self.assertEqual(ui.resolve_lang('ru-RU'), 'ru')

    def test_default_english(self) -> None:
        self.assertEqual(ui.resolve_lang(None), 'en')
        self.assertEqual(ui.resolve_lang('de'), 'en')


class TestInlineKeyboards(unittest.TestCase):
    def test_home_keyboard_has_cash_and_usdt(self) -> None:
        markup = ui.home_inline_keyboard('en')
        data = [
            button.callback_data
            for row in markup.inline_keyboard
            for button in row
        ]
        self.assertIn('mode:cash', data)
        self.assertIn('mode:usdt', data)

    def test_cities_keyboard_has_nav_and_allowed_cities(self) -> None:
        markup = ui.cities_inline_keyboard('en')
        data = [
            button.callback_data
            for row in markup.inline_keyboard
            for button in row
        ]
        self.assertIn('city:Moscow', data)
        self.assertIn('city:SPB', data)
        self.assertIn('nav:back', data)
        self.assertIn('nav:home', data)

    def test_currencies_keyboard_has_stats_and_nav(self) -> None:
        markup = ui.currencies_inline_keyboard('en')
        data = [
            button.callback_data
            for row in markup.inline_keyboard
            for button in row
        ]
        self.assertIn('currency:USD', data)
        self.assertIn('currency:CNY', data)
        self.assertIn('currency:CHF', data)
        self.assertIn('currency:TRY', data)
        self.assertIn('stats', data)
        self.assertIn('nav:back', data)
        self.assertIn('nav:home', data)

    def test_result_keyboard_has_refresh(self) -> None:
        markup = ui.result_inline_keyboard('ru')
        data = [
            button.callback_data
            for row in markup.inline_keyboard
            for button in row
        ]
        self.assertIn('nav:refresh', data)
        self.assertIn('nav:back', data)
        self.assertIn('nav:home', data)

    def test_buttons_are_inline_keyboard_buttons(self) -> None:
        markup = ui.home_inline_keyboard('ru')
        first = markup.inline_keyboard[0][0]
        self.assertIsInstance(first, InlineKeyboardButton)


class TestCallbackValidation(unittest.TestCase):
    def test_allowed_city_and_currency(self) -> None:
        self.assertEqual(ui.parse_city('city:Moscow'), 'Moscow')
        self.assertEqual(ui.parse_currency('currency:EUR'), 'EUR')
        self.assertEqual(ui.parse_currency('currency:CNY'), 'CNY')
        self.assertIsNone(ui.parse_city('city:Hack'))
        self.assertIsNone(ui.parse_currency('currency:XYZ'))

    def test_home_can_show_last_and_favorite(self) -> None:
        prefs = {
            'last_city': 'Moscow',
            'last_currency': 'USD',
            'fav_city': 'SPB',
            'fav_currency': 'EUR',
        }
        markup = ui.home_inline_keyboard('en', prefs)
        data = [
            button.callback_data
            for row in markup.inline_keyboard
            for button in row
        ]
        self.assertIn('last:open', data)
        self.assertIn('fav:open', data)
        self.assertIn('alerts:list', data)

    def test_result_keyboard_has_actions(self) -> None:
        markup = ui.result_inline_keyboard('en', 'quotes')
        data = [
            button.callback_data
            for row in markup.inline_keyboard
            for button in row
        ]
        self.assertIn('calc:open', data)
        self.assertIn('alert:open', data)
        self.assertIn('fav:set', data)
        self.assertIn('where:open', data)


if __name__ == '__main__':
    unittest.main()
