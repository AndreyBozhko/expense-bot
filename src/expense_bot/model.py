"""Data representations."""
from dataclasses import dataclass
from enum import Enum, auto


class Category(Enum):
    """Expense category."""

    EARN = auto()
    SPEND = auto()


EARN, SPEND = list(Category)


@dataclass
class ExpenseItem:
    """Common expense item.

    Attributes:
        amt (float):    amount
        vnd (str):      vendor
        cat (Category): item category
    """

    amt: float
    vnd: str
    cat: Category = SPEND
