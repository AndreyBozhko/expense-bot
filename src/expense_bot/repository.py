"""Storage for expense records."""

import logging
from abc import ABC, abstractmethod
from datetime import date
from typing import Iterable, Type

from aiogram.utils.mixins import ContextInstanceMixin

from .model import ExpenseItem
from .utils import FactoryMixin, setup_logging

setup_logging()
logger = logging.getLogger()


class Repository(ABC, ContextInstanceMixin, FactoryMixin):
    """Base repository."""

    @classmethod
    def current(cls: Type["Repository"]) -> "Repository":
        """Get registered instance of this class,
        or raise an exception if not found."""
        try:
            return cls.get_current(no_error=False)
        except LookupError:
            raise LookupError(
                f"{cls.__name__} is not configured..."
            ) from None

    @abstractmethod
    def get_all(self, *, dt: date) -> Iterable[ExpenseItem]:
        """Get expense report for a given date"""

    @abstractmethod
    def add(self, item: ExpenseItem, /, *, dt: date):
        """Record a new expense"""
