"""Lambda function handler."""
import asyncio
import json
import logging
from typing import TYPE_CHECKING

import boto3

import expense_bot as bot
from expense_bot import Repository, setup_logging
from expense_bot.secrets import provides

if TYPE_CHECKING:
    from awslambdaric.lambda_context import LambdaContext

setup_logging()
logger = logging.getLogger()


@provides(secret="g-service-acct")
def service_acct_credentials():
    secret_name = "expenseBot/credentials/gsheet"

    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager")

    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response["SecretString"])


Repository.set_current(Repository.new("GoogleSheets"))


def handler(event: dict, context: "LambdaContext"):
    """Entry point for the Lambda function."""
    logger.info("Expense Bot (version %s) started!", bot.__version__)
    return asyncio.run(bot.handle_lambda_event(event))
