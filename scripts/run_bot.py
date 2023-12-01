"""Run the bot in a long-polling mode."""
import asyncio
import json

from expense_bot import Repository
from expense_bot.bot import bot, dp
from expense_bot.secrets import provides


@provides(secret="g-service-acct")
def creds():
    with open("bot-credentials.json", encoding="utf-8") as fin:
        return json.load(fin)


async def main():
    Repository.set_current(Repository.new("InMemory"))
    await dp.start_polling(
        bot, skip_updates=True, allowed_updates=["message", "callback_query"]
    )


if __name__ == "__main__":
    asyncio.run(main())
