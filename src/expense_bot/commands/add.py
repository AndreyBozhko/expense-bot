"""Implementation of /add command."""
import logging
from datetime import date
from random import choice

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import Message
from aiogram.types.reply_keyboard import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from ..model import EARN, SPEND, ExpenseItem
from ..repository import Repository
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
        await Add.amount.set()
        await message.answer("Amount in $?")

    income_descriptions = ["Paycheck", "Cashback"]

    @dp.message_handler(state=Add.amount)
    @default_message_logging
    async def cmd_add_state1(message: Message, state: FSMContext):
        await state.update_data(amount=float(message.text))
        await Add.next()
        await message.answer(
            "Description?",
            reply_markup=ReplyKeyboardMarkup(
                one_time_keyboard=True,
                resize_keyboard=True,
                keyboard=[
                    [
                        KeyboardButton(text=desc)
                        for desc in income_descriptions
                    ]
                ],
            ),
        )

    @dp.message_handler(state=Add.vendor)
    @default_message_logging
    async def cmd_add_state2(message: Message, state: FSMContext):
        data = await state.get_data()

        amt, vnd = data["amount"], message.text
        item = ExpenseItem(
            amt,
            vnd,
            EARN if vnd in income_descriptions else SPEND,
        )

        Repository.current().add(item, dt=date.today())

        await message.answer(
            choice(["🎉", "🥳", "🙌", "✔️", "💾"]),
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.finish()
