"""Utilities to handle secrets."""

from functools import cache
from typing import Any, Callable


class SecretsProvider:
    """Central place to store and retrieve secrets."""

    def __init__(self):
        self._providers = {}

    def __getitem__(self, key: str) -> Any:
        return self._providers[key]()

    def register(self, *, secret: str):
        """Register callable as a provider
        of a secret with a given name."""

        def wrapper(func: Callable[[], Any]):
            self._providers[secret] = cache(func)
            return func

        return wrapper


secrets = SecretsProvider()
provides = secrets.register

__all__ = [
    "provides",
    "secrets",
]
