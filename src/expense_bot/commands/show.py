"""Implementation of /show command."""
import logging
from random import choice

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.types.inline_keyboard import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.types.message_entity import MessageEntity

from ..repository import Repository
from ..utils import parse_datetime
from .common import auth_required, default_message_logging

logger = logging.getLogger()


async def _do_show(message: Message, dt_str: str):
    date_time = parse_datetime(dt_str)
    items = Repository.current().get_all(dt=date_time.date())

    if not items:
        await message.answer(choice(["🤷‍♂️", "😴", "😪"]))

    for item in items:
        vnd, amt = item.vnd, f"${item.amt:.2f}"
        await message.answer(
            vnd + ": " + amt,
            protect_content=True,
            entities=[
                MessageEntity("bold", 0, len(vnd)),
                MessageEntity("code", len(vnd) + 2, len(amt)),
            ],
        )


class Show(StatesGroup):
    """States for /show command flow."""

    selected_date = State()


def configure_show_command(dp: Dispatcher):
    """Configure FSM behind /show command."""

    @dp.message_handler(auth_required, commands=["show"])
    @default_message_logging
    async def cmd_show_state0(message: Message):
        args = message.get_args()
        if args:
            await _do_show(message, args)
            return

        await Show.selected_date.set()
        await message.answer(
            "Which date?",
            reply_markup=InlineKeyboardMarkup().add(
                *[
                    InlineKeyboardButton(data, callback_data=data)
                    for data in ["today", "yesterday"]
                ]
            ),
        )

    @dp.message_handler(auth_required, state=Show.selected_date)
    @default_message_logging
    async def cmd_show_state1(message: Message, state: FSMContext):
        await _do_show(message, message.text)
        await state.finish()

    @dp.callback_query_handler(auth_required, state=Show.selected_date)
    async def cb_show_state1(callback: CallbackQuery, state: FSMContext):
        msg = callback.message
        await msg.answer(callback.data)

        msg.text = callback.data
        await cmd_show_state1(msg, state)
