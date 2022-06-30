"""Delete bot webhook."""
import asyncio

from expense_bot import bot


async def main():
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        return await bot.get_webhook_info()
    finally:
        await bot.close()


if __name__ == "__main__":
    print(asyncio.run(main()))
