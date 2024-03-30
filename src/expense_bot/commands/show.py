"""Implementation of /show command."""

import logging
from random import choice

from aiogram import Dispatcher
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.types.inline_keyboard_markup import InlineKeyboardMarkup
from aiogram.utils.formatting import Bold, Code, Italic, Text

from ..repository import Repository
from ..utils import parse_date
from .common import auth_required, default_message_logging

logger = logging.getLogger()


async def _do_show(message: Message, dt_str: str):
    dt = parse_date(dt_str)
    items = Repository.current().get_all(dt=dt)

    if not items:
        await message.answer(choice(["🤷‍♂️", "😴", "😪"]))

    for item in items:
        vnd, amt = item.vnd, f"${item.amt:.2f}"
        msg = Text(Bold(vnd), ": ", Code(amt))
        await message.answer(
            protect_content=True,
            **msg.as_kwargs(),
        )


class Show(StatesGroup):
    """States for /show command flow."""

    selected_date = State()


def configure_show_command(dp: Dispatcher):
    """Configure FSM behind /show command."""

    @dp.message(auth_required, Command("show"))
    @default_message_logging
    async def cmd_show_state0(
        message: Message, command: CommandObject, state: FSMContext
    ):
        args = command.args
        if args:
            await _do_show(message, args)
            return

        await state.set_state(Show.selected_date)
        await message.answer(
            "Which date?",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text=data, callback_data=data)
                        for data in ["today", "yesterday"]
                    ]
                ]
            ),
        )

    @dp.message(auth_required, StateFilter(Show.selected_date))
    @default_message_logging
    async def cmd_show_state1(message: Message, state: FSMContext):
        await _do_show(message, message.text or "")
        await state.clear()

    @dp.callback_query(auth_required, StateFilter(Show.selected_date))
    async def cb_show_state1(callback: CallbackQuery, state: FSMContext):
        msg = callback.message
        assert msg, "must not be None"

        text = Text("👉 ", Italic(callback.data))
        await msg.answer(**text.as_kwargs())

        msg = msg.model_copy(update={"text": callback.data})
        await cmd_show_state1(msg, state)
