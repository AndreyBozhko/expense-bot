"""Implementation of /add command."""
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

from ..model import EARN, SPEND, ExpenseItem
from ..repository import Repository
from ..utils import parse_datetime
from .common import auth_required, default_message_logging

logger = logging.getLogger()


class Add(StatesGroup):
    """States for /add command flow."""

    amount = State()
    vendor = State()


def configure_add_command(dp: Dispatcher):
    """Configure FSM behind /add command."""

    @dp.message_handler(auth_required, commands=["add"])
    @default_message_logging
    async def cmd_add_state0(message: Message):
        dt_str = message.get_args() or "today"
        dt = parse_datetime(dt_str).date()

        await Add.amount.set()

        state = dp.current_state()
        await state.update_data(dt=dt)

        await message.answer("Amount in $?")

    income_descriptions = ["Paycheck", "Cashback"]

    @dp.message_handler(auth_required, state=Add.amount)
    @default_message_logging
    async def cmd_add_state1(message: Message, state: FSMContext):
        await state.update_data(amount=float(message.text))
        await Add.next()
        await message.answer(
            "Description?",
            reply_markup=InlineKeyboardMarkup().add(
                *[
                    InlineKeyboardButton(desc, callback_data=desc)
                    for desc in income_descriptions
                ],
            ),
        )

    @dp.message_handler(auth_required, state=Add.vendor)
    @default_message_logging
    async def cmd_add_state2(message: Message, state: FSMContext):
        data = await state.get_data()

        amt, dt, vnd = data["amount"], data["dt"], message.text
        item = ExpenseItem(
            amt,
            vnd,
            EARN if vnd in income_descriptions else SPEND,
        )

        Repository.current().add(item, dt=dt)

        await message.answer(choice(["🎉", "🥳", "🙌", "✔️", "💾"]))
        await state.finish()

    @dp.callback_query_handler(state=Add.vendor)
    async def cb_add_state2(callback: CallbackQuery, state: FSMContext):
        msg = callback.message
        await msg.answer(callback.data)

        msg.text = callback.data
        await cmd_add_state2(msg, state)
