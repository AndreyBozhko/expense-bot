"""Storage implementations."""

from collections import defaultdict
from datetime import date
from typing import Iterable

from ..model import ExpenseItem
from ..repository import Repository
from ..utils import setup_logging
from .google import GoogleSheets

setup_logging()

_StorageType = dict[date, list[ExpenseItem]]


class InMemory(Repository):
    """In-memory repository."""

    def __init__(self):
        self._storage: _StorageType = defaultdict(list)

    def get_all(self, *, dt: date) -> Iterable[ExpenseItem]:
        return self._storage.get(dt) or []

    def add(self, item: ExpenseItem, /, *, dt: date):
        self._storage[dt].append(item)


__all__ = [
    "GoogleSheets",
    "InMemory",
]
