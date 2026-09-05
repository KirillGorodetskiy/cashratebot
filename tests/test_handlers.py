import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ParseMode

import handlers


def make_user(user_id: int = 7, language_code: str = 'en'):
    user = MagicMock()
    user.id = user_id
    user.language_code = language_code
    return user


def make_message():
    message = MagicMock()
    sent = MagicMock()
    sent.edit_text = AsyncMock()
    sent.delete = AsyncMock()
    message.reply_text = AsyncMock(return_value=sent)
    return message


def make_update_with_message(user=None, text='/start'):
    user = user or make_user()
    update = MagicMock()
    update.effective_user = user
    update.message = make_message()
    update.message.text = text
    update.callback_query = None
    return update


def make_update_with_query(data: str, user=None):
    user = user or make_user()
    query = MagicMock()
    query.data = data
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    query.from_user = user
    query.message = make_message()
    update = MagicMock()
    update.effective_user = user
    update.callback_query = query
    update.message = None
    return update, query


def make_context(user_data=None):
    context = MagicMock()
    context.user_data = user_data if user_data is not None else {}
    return context


class TestStartHandler(unittest.IsolatedAsyncioTestCase):
    @patch('handlers.get_user_prefs', return_value={})
    @patch('handlers.save_new_user_data_in_db')
    async def test_start_sends_html_and_clears_reply_keyboard(
        self,
        mock_save,
        _prefs,
    ) -> None:
        update = make_update_with_message()
        context = make_context()

        await handlers.start(update, context)

        mock_save.assert_called_once()
        calls = update.message.reply_text.await_args_list
        home_kwargs = None
        removed_old_keyboard = False
        for call in calls:
            markup = call.kwargs['reply_markup']
            if isinstance(markup, ReplyKeyboardRemove):
                removed_old_keyboard = True
                continue
            home_kwargs = call.kwargs
        self.assertTrue(removed_old_keyboard)
        self.assertIsNotNone(home_kwargs)
        self.assertEqual(home_kwargs['parse_mode'], ParseMode.HTML)
        self.assertIn('<blockquote expandable>', home_kwargs['text'])
        self.assertIsInstance(
            home_kwargs['reply_markup'],
            InlineKeyboardMarkup,
        )
        data = [
            button.callback_data
            for row in home_kwargs['reply_markup'].inline_keyboard
            for button in row
        ]
        self.assertIn('mode:cash', data)
        self.assertIn('mode:usdt', data)
        self.assertEqual(context.user_data['step'], 'home')
        self.assertEqual(context.user_data['lang'], 'en')


class TestCallbackFlow(unittest.IsolatedAsyncioTestCase):
    @patch('handlers.save_new_user_data_in_db')
    async def test_cash_edits_same_message(self, mock_save) -> None:
        update, query = make_update_with_query('mode:cash')
        context = make_context({'lang': 'en', 'step': 'home'})

        await handlers.handle_callback(update, context)

        query.edit_message_text.assert_awaited()
        query.message.reply_text.assert_not_awaited()
        kwargs = query.edit_message_text.await_args.kwargs
        self.assertEqual(kwargs['parse_mode'], ParseMode.HTML)
        self.assertEqual(context.user_data['step'], 'cities')
        self.assertEqual(context.user_data['mode'], 'cash')

    @patch('handlers.fetch_usdt_rub_rates')
    @patch('handlers.build_message', return_value='<b>USDT</b>')
    async def test_usdt_edits_and_keeps_state(
        self,
        mock_build,
        mock_fetch,
    ) -> None:
        mock_fetch.return_value = {'rates': {}}
        update, query = make_update_with_query('mode:usdt')
        context = make_context({
            'lang': 'en',
            'step': 'home',
            'city': 'Moscow',
        })

        await handlers.handle_callback(update, context)

        query.edit_message_text.assert_awaited()
        self.assertEqual(context.user_data['city'], 'Moscow')
        self.assertEqual(context.user_data['step'], 'usdt')

    async def test_invalid_city_is_rejected(self) -> None:
        update, query = make_update_with_query('city:Hack')
        context = make_context({'lang': 'en', 'step': 'cities'})

        await handlers.handle_callback(update, context)

        query.answer.assert_awaited()
        query.edit_message_text.assert_not_awaited()

    async def test_city_keeps_previous_state(self) -> None:
        update, query = make_update_with_query('city:SPB')
        context = make_context({
            'lang': 'en',
            'step': 'cities',
            'mode': 'cash',
        })

        await handlers.handle_callback(update, context)

        self.assertEqual(context.user_data['city'], 'SPB')
        self.assertEqual(context.user_data['mode'], 'cash')
        self.assertEqual(context.user_data['step'], 'currencies')

    @patch('handlers.get_user_prefs', return_value={})
    async def test_home_resets_to_menu(self, _prefs) -> None:
        update, query = make_update_with_query('nav:home')
        context = make_context({
            'lang': 'en',
            'step': 'quotes',
            'city': 'Moscow',
            'currency': 'USD',
        })

        await handlers.handle_callback(update, context)

        self.assertEqual(context.user_data['step'], 'home')
        query.edit_message_text.assert_awaited()

    async def test_back_from_currencies_goes_to_cities(self) -> None:
        update, query = make_update_with_query('nav:back')
        context = make_context({
            'lang': 'en',
            'step': 'currencies',
            'city': 'Moscow',
        })

        await handlers.handle_callback(update, context)

        self.assertEqual(context.user_data['step'], 'cities')


if __name__ == '__main__':
    unittest.main()
