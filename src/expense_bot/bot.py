"""Bot configuration."""
import json
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update

from .commands import (
    configure_add_command,
    configure_cancel_command,
    configure_error_handling,
    configure_show_command,
    configure_start_command,
)
from .secrets import provides, secrets
from .utils import setup_logging

setup_logging()
logger = logging.getLogger()


@provides(secret="bot-token")
def bot_token():
    """Read token from environment, otherwise read from file."""
    try:
        return os.environ["BOT_TOKEN"]
    except KeyError:
        with open("bot.token", encoding="utf-8") as fin:
            return fin.read().strip()


bot = Bot(token=secrets["bot-token"])
dp = Dispatcher(storage=MemoryStorage())

# start - Start conversation
# add - Record an expense item
# show - Show expenses for a certain date
# cancel - Cancel current operation
configure_start_command(dp)
configure_cancel_command(dp)
configure_add_command(dp)
configure_show_command(dp)
configure_error_handling(dp)


async def handle_lambda_event(event: dict):
    """Process the webhook payload sent to the Lambda function
    as a single :type:`aiogram.types.Update` event.

    Note: this function is NOT stateless - but for now
    it's OK to assume that AWS Lambda would reuse the same
    runtime for handling a few requests back-to-back."""
    values = json.loads(event["body"])
    update = Update.model_construct(**values)
    await dp.feed_update(bot, update)
