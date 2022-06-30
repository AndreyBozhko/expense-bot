"""Bot configuration."""
import json
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
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
dp = Dispatcher(bot, storage=MemoryStorage())

# start - Start conversation
# add - Record an expense item
# show - Show expenses for a certain date
# cancel - Cancel current operation
configure_start_command(dp)
configure_cancel_command(dp)
configure_add_command(dp)
configure_show_command(dp)
configure_error_handling(dp)

Dispatcher.set_current(dp)
Bot.set_current(dp.bot)


async def handle_lambda_event(event: dict):
    """Process the webhook payload sent to the Lambda function
    as a single :type:`aiogram.types.Update` event."""
    update = Update.to_object(json.loads(event["body"]))
    await dp.process_update(update)
