"""Implementation of /show command."""
import logging
from contextlib import suppress
from datetime import datetime, timedelta
from random import choice

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import Message
from aiogram.types.message_entity import MessageEntity
from aiogram.types.reply_keyboard import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from ..repository import Repository
from .common import auth_required, default_message_logging

logger = logging.getLogger()

FORMATS = ["%Y-%m-%d", "%Y%m%d", "%m/%d/%Y", "%m/%d/%y"]


def parse_datetime(value: str) -> datetime:
    """Parse provided string as date."""
    if value == "today":
        return datetime.today()
    if value == "yesterday":
        return datetime.today() - timedelta(days=1)

    for fmt in FORMATS:
        with suppress(ValueError):
            return datetime.strptime(value, fmt)
    raise ValueError(
        f"time data '{value}' does not match any of the formats {FORMATS}"
    )


async def _do_show(message: Message, dt_str: str):
    date_time = parse_datetime(dt_str)
    items = Repository.current().get_all(dt=date_time.date())

    if not items:
        await message.answer(
            choice(["🤷‍♂️", "😴", "😪"]),
            reply_markup=ReplyKeyboardRemove(),
        )

    for item in items:
        vnd, amt = item.vnd, f"${item.amt:.2f}"
        await message.answer(
            vnd + ": " + amt,
            protect_content=True,
            entities=[
                MessageEntity("bold", 0, len(vnd)),
                MessageEntity("code", len(vnd) + 2, len(amt)),
            ],
            reply_markup=ReplyKeyboardRemove(),
        )


class Show(StatesGroup):
    """States for /show command flow."""

    selected_date = State()


def configure_show_command(dp: Dispatcher):
    """Configure FSM behind /show command."""

    @dp.message_handler(auth_required, commands=["show"])
    @default_message_logging
    async def cmd_show_state0(message: Message):
        if message.get_args():
            await _do_show(message, message.text.split(maxsplit=1)[-1])
            return

        await Show.selected_date.set()
        await message.answer(
            "Which date?",
            reply_markup=ReplyKeyboardMarkup(
                one_time_keyboard=True,
                resize_keyboard=True,
                keyboard=[
                    [
                        KeyboardButton(text="today"),
                        KeyboardButton(text="yesterday"),
                    ]
                ],
            ),
        )

    @dp.message_handler(state=Show.selected_date)
    @default_message_logging
    async def cmd_show_state1(message: Message, state: FSMContext):
        await _do_show(message, message.text)
        await state.finish()
