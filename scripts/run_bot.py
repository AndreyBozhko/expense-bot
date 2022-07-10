"""Run the bot in a long-polling mode."""
import json

from aiogram import executor

from expense_bot import Repository
from expense_bot.bot import dp
from expense_bot.secrets import provides


@provides(secret="g-service-acct")
def creds():
    with open("bot-credentials.json", encoding="utf-8") as fin:
        return json.load(fin)


if __name__ == "__main__":
    Repository.set_current(Repository.new("InMemory"))
    executor.start_polling(
        dp, skip_updates=True, allowed_updates=["message", "callback_query"]
    )
