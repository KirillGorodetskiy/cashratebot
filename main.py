import logging
import os

from dotenv import load_dotenv
from telegram.error import TelegramError
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
)

from db_manager import db_init
from handlers import (
    cash_command,
    handle_callback,
    help_command,
    start,
    usdt_command,
)
import redis_client
import ui

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s: - %(message)s',
    filename='app.log',
    filemode='a',
)

logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')


async def on_startup(app) -> None:
    await app.bot.set_my_commands(ui.bot_commands('en'))
    await app.bot.set_my_commands(
        ui.bot_commands('ru'),
        language_code='ru',
    )
    try:
        await app.bot.set_my_short_description(
            ui.BOT_SHORT_DESCRIPTION['en'],
        )
        await app.bot.set_my_short_description(
            ui.BOT_SHORT_DESCRIPTION['ru'],
            language_code='ru',
        )
        await app.bot.set_my_description(ui.BOT_DESCRIPTION['en'])
        await app.bot.set_my_description(
            ui.BOT_DESCRIPTION['ru'],
            language_code='ru',
        )
    except TelegramError as exc:
        logger.error('Could not update bot profile texts: %s', exc)


def build_application():
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .post_init(on_startup)
        .build()
    )
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('cash', cash_command))
    app.add_handler(CommandHandler('usdt', usdt_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    return app


def main() -> None:
    logging.info('Entry point...')
    db_init()
    redis_client.redis_client_init()
    app = build_application()
    logger.info('Bot is running....')
    print('Bot is running...')
    app.run_polling()


if __name__ == '__main__':
    main()
