"""Internal utilities in order to be used by fieldenum implementation.

The functions and classes are not meant to be used by users.
This things can be modified, deleted, or added without notice or major version change.
"""

from __future__ import annotations

import copyreg
import typing
from contextlib import suppress


def unpickle(cls, name: str, state: tuple | dict | None):
    variant = getattr(cls, name)
    if state is None:
        return variant
    elif isinstance(state, tuple):
        return variant(*state)
    else:
        return variant(**state)


copyreg.constructor(unpickle)  # type: ignore # suppressing incorrect type checker error


class NotAllowed:
    def __init__(self, message: str | None = None, name: str | None = None):
        self.error_message = message
        if name is not None:
            self.name = name

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if objtype is None:
            return self

        raise TypeError(self.error_message or f"The method/attribute {self.name!r} is not allowed to be used.")


class OneTimeSetter:
    def __set_name__(self, owner, name):
        self.private_name = f"__original_{name}"

    def __get__(self, obj, objtype=None):
        return getattr(obj, self.private_name)

    def __set__(self, obj, value):
        if hasattr(obj, self.private_name):
            raise TypeError(f"Attribute `{self.private_name.lstrip('__original_')}` is frozen thus cannot mutate.")
        setattr(obj, self.private_name, value)


class ParamlessSingletonMeta(type):
    """Singleton implementation for class that does not require any parameter."""

    def __call__(cls):
        with suppress(AttributeError):
            return cls._instance

        cls._instance = super().__call__()
        return cls._instance
