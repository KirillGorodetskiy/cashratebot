import logging

# Basic logger configuration
logging.basicConfig(
    level=logging.INFO,  
    format='%(asctime)s - %(levelname)s - %(name)s: - %(message)s',
    filename='app.log',  # log to file
    filemode='a'         # Append to file (or 'w' to overwrite)
)

# Create a logger
logger = logging.getLogger(__name__)

logger.info("Before imports...")

from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
import os
from dotenv import load_dotenv
from prompts import*
from handlers import handle_callback, start
from db_manager import db_init
import redis_client



# Load .env variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Build and run the bot
def main():
    logging.info("Entry point...")
    db_init()
    redis_client.redis_client_init()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(CommandHandler("start", start))
    
    logger.info("Bot is running....")

    print("Bot is running...")
    app.run_polling()  # ❗ This is NOT awaited — it handles its own loop

if __name__ == "__main__":
    main()
