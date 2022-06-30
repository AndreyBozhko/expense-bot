"""Utility functions and helpers."""
import logging
import os
from typing import Any, Iterable, Type, TypeVar


def setup_logging():
    """Configure logging level."""
    logging.basicConfig(
        level=getattr(
            logging, os.environ.get("LOG_LEVEL", "INFO"), logging.INFO
        ),
        force=True,
    )


setup_logging()
logger = logging.getLogger()

_T = TypeVar("_T")


def all_subclasses(cls: type) -> Iterable[type]:
    """Return all subclasses of a given class."""
    for subcls in cls.__subclasses__():
        yield from all_subclasses(subcls)
        yield subcls


class FactoryMixin:  # pylint: disable=R0903
    """Mixin that provides factory methods."""

    @classmethod
    def new(cls: Type[_T], type_name: str, *args: Any, **kwargs: Any) -> _T:
        """Instantiate a subclass with matching name."""
        for subcls in all_subclasses(cls):
            if subcls.__name__ == type_name:
                logger.info(
                    "Instantiating %s subclass: %s", cls.__name__, subcls
                )
                return subcls(*args, **kwargs)
        raise ValueError(
            f"Could not find subclass of {cls.__name__} for name: {type_name}"
        )
