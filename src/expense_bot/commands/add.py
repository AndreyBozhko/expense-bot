"""Implementation of /add command."""
import logging
from random import choice

from aiogram import Dispatcher
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.types.inline_keyboard_markup import InlineKeyboardMarkup
from aiogram.utils.formatting import Italic, Text

from ..model import EARN, SPEND, ExpenseItem
from ..repository import Repository
from ..utils import parse_date
from .common import auth_required, default_message_logging

logger = logging.getLogger()


class Add(StatesGroup):
    """States for /add command flow."""

    amount = State()
    vendor = State()


def configure_add_command(dp: Dispatcher):
    """Configure FSM behind /add command."""

    @dp.message(auth_required, Command("add"))
    @default_message_logging
    async def cmd_add_state0(
        message: Message, command: CommandObject, state: FSMContext
    ):
        dt_str = command.args or "today"
        dt = parse_date(dt_str)

        await state.set_state(Add.amount)
        await state.update_data(dt=dt)

        await message.answer("Amount in $?")

    income_descriptions = ["Paycheck", "Cashback"]

    @dp.message(auth_required, StateFilter(Add.amount))
    @default_message_logging
    async def cmd_add_state1(message: Message, state: FSMContext):
        await state.update_data(amount=float(message.text or ""))
        await state.set_state(Add.vendor)
        await message.answer(
            "Description?",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text=desc, callback_data=desc)
                        for desc in income_descriptions
                    ],
                ]
            ),
        )

    @dp.message(auth_required, StateFilter(Add.vendor))
    @default_message_logging
    async def cmd_add_state2(message: Message, state: FSMContext):
        data = await state.get_data()

        amt, dt, vnd = data["amount"], data["dt"], message.text or ""
        item = ExpenseItem(
            amt,
            vnd,
            EARN if vnd in income_descriptions else SPEND,
        )

        Repository.current().add(item, dt=dt)

        await message.answer(choice(["🎉", "🥳", "🙌", "✔️", "💾"]))
        await state.clear()

    @dp.callback_query(auth_required, StateFilter(Add.vendor))
    async def cb_add_state2(callback: CallbackQuery, state: FSMContext):
        msg = callback.message
        assert msg, "must not be None"

        text = Text("👉 ", Italic(callback.data))
        await msg.answer(**text.as_kwargs())

        msg = msg.model_copy(update={"text": callback.data})
        await cmd_add_state2(msg, state)
