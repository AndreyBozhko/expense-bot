"""Common bot configurations."""

import logging
from functools import wraps
from typing import Any, Callable, Coroutine, Union, overload

from aiogram import Dispatcher, F
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ErrorEvent, Message
from aiogram.utils.formatting import Code, Text, TextMention

logger = logging.getLogger()


class AccessDenied(Exception):
    """Exception to indicate that the user is not authorized."""


def auth_required(msg: Union[CallbackQuery, Message]) -> bool:
    """Allow messages from a single user only."""
    user = msg.from_user
    if not user or user.id != 288450274:
        raise AccessDenied("Unauthorized!")
    return True


@overload
def default_message_logging(coro: Callable[[Message], Coroutine]): ...


@overload
def default_message_logging(
    coro: Callable[[Message, FSMContext], Coroutine],
): ...


@overload
def default_message_logging(
    coro: Callable[[Message, CommandObject, FSMContext], Coroutine],
): ...


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

    @dp.errors()
    async def process_error(error: ErrorEvent):
        """Handle exceptions."""
        upd, exc = error.update, error.exception
        msg = Text(
            "Something went wrong...",
            "\n\n",
            Code(f"{exc.__class__.__name__}: {exc}"),
        )

        logger.warning(msg.render()[0])
        if upd.message:
            await upd.message.answer(**msg.as_kwargs())

        # dispatcher won't re-raise the exception
        # if a truthy value is returned from handler
        return exc

    @dp.message(auth_required)
    @default_message_logging
    async def cmd_unrecognized(message: Message):
        await message.answer("Command not recognized :(")


def configure_start_command(dp: Dispatcher):
    """Configure logic behind /start command."""

    @dp.message(auth_required, Command("start"))
    @default_message_logging
    async def cmd_start(message: Message):
        """Handler for `start` command."""
        user = message.from_user
        assert user, "must not be None"

        text = Text(
            "Hi ",
            TextMention(user.full_name, user=user),
            "! 👋\nI'm your personal expense tracking bot!",
        )
        await message.answer(**text.as_kwargs())


def configure_cancel_command(dp: Dispatcher):
    """Configure logic behind /cancel command."""

    @dp.message(auth_required, StateFilter("*"), Command("cancel"))
    @dp.message(auth_required, F.text == "cancel", StateFilter("*"))
    @default_message_logging
    async def cmd_cancel(message: Message, state: FSMContext):
        current_state = await state.get_state()
        if current_state is None:
            return

        logger.info("Cancelling state %r", current_state)

        operation = current_state.lower().split(":")[0]

        await state.clear()
        await message.answer(f"Operation /{operation} cancelled")
