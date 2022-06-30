"""Set bot webhook."""
import asyncio
from typing import Iterable

import boto3

from expense_bot import bot

client = boto3.client("apigatewayv2")


def get_api_by_name(name: str) -> tuple[str, str]:
    apis = client.get_apis()
    for api in apis["Items"]:
        if api["Name"] == name:
            return api["ApiId"], api["ApiEndpoint"]

    raise ValueError(f"No API found for name: <{name}>")


def get_routes_for_api(api_id: str) -> Iterable[tuple[str, str]]:
    routes = client.get_routes(ApiId=api_id)
    for route in routes["Items"]:
        method, path = route["RouteKey"].split()
        yield method, path


async def main():
    try:
        api_id, api_url = get_api_by_name("expenseBotAPI")
        _, route = next(get_routes_for_api(api_id))

        await bot.set_webhook(api_url + route, allowed_updates=["message"])
        return await bot.get_webhook_info()
    finally:
        await bot.close()


if __name__ == "__main__":
    print(asyncio.run(main()))
