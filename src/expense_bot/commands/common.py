"""Common bot configurations."""
import logging
from functools import wraps
from typing import Any, Callable, Coroutine, Union, overload

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, Message, Update
from aiogram.types.message_entity import MessageEntity

logger = logging.getLogger()


class AccessDenied(Exception):
    """Exception to indicate that the user is not authorized."""


def auth_required(msg: Union[CallbackQuery, Message]) -> bool:
    """Allow messages from a single user only."""
    if msg.from_user.id != 288450274:
        raise AccessDenied("Unauthorized!")
    return True


@overload
def default_message_logging(coro: Callable[[Message], Coroutine]):
    ...


@overload
def default_message_logging(coro: Callable[[Message, FSMContext], Coroutine]):
    ...


def default_message_logging(coro: Callable[..., Coroutine]):
    """Inject pre- and post-processing logging into a handler."""

    @wraps(coro)
    async def wrapper(message: Message, *args: Any, **kwargs: Any):
        try:
            logger.info(
                "Message %s, chat %s: `%s` handler dispatched",
                message.message_id,
                message.chat.id,
                coro.__name__,
            )

            return await coro(message, *args, **kwargs)
        finally:
            logger.info(
                "Message %s, chat %s: `%s` handler done",
                message.message_id,
                message.chat.id,
                coro.__name__,
            )

    return wrapper


def configure_error_handling(dp: Dispatcher):
    """Configure bot handling of errors."""

    @dp.errors_handler()
    async def process_error(upd: Update, exc: Exception):
        """Handle exceptions."""
        msg = ["Something went wrong...", f"{exc.__class__.__name__}: {exc}"]

        logger.warning("%s %s", *msg)
        if upd.message:
            await upd.message.answer(
                "\n\n".join(msg),
                entities=[
                    MessageEntity("code", len(msg[0]) + 2, len(msg[1]))
                ],
            )

        # dispatcher won't re-raise the exception
        # if a truthy value is returned from handler
        return exc

    @dp.message_handler(auth_required)
    @default_message_logging
    async def cmd_unrecognized(message: Message):
        await message.answer("Command not recognized :(")


def configure_start_command(dp: Dispatcher):
    """Configure logic behind /start command."""

    @dp.message_handler(auth_required, commands=["start"])
    @default_message_logging
    async def cmd_start(message: Message):
        """Handler for `start` command."""
        mention = message.from_user.mention
        await message.answer(
            f"Hi {mention}! 👋\nI'm your personal expense tracking bot!",
            entities=[
                MessageEntity("mention", 3, len(mention)),
            ],
        )


def configure_cancel_command(dp: Dispatcher):
    """Configure logic behind /cancel command."""

    @dp.message_handler(auth_required, state="*", commands="cancel")
    @dp.message_handler(
        auth_required, Text(equals="cancel", ignore_case=True), state="*"
    )
    @default_message_logging
    async def cmd_cancel(message: Message, state: FSMContext):
        current_state = await state.get_state()
        if current_state is None:
            return

        logger.info("Cancelling state %r", current_state)

        operation = current_state.lower().split(":")[0]

        await state.finish()
        await message.answer(f"Operation /{operation} cancelled")
