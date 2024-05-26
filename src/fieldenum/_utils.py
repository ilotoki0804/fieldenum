"""Internal utilities in order to be used by fieldenum implementation.

The functions and classes are not meant to be used by users.
This things can be modified, deleted, or added without notice or major version change.
"""

from __future__ import annotations

import copyreg
import typing
from contextlib import suppress

from .exceptions import NotAllowedError


def unpickle(cls, name: str, state: tuple | dict | None):
    case = getattr(cls, name)
    if state is None:
        return case
    elif isinstance(state, tuple):
        return case(*state)
    else:
        return case(**state)


copyreg.constructor(unpickle)  # type: ignore # supressing incorrect type checker error


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

        raise NotAllowedError(self.error_message or f"The method/attribute {self.name!r} is not allowed to be used.")


class KindError:
    def __init__(self, message: str):
        self.error_message = message

    def __set_name__(self, owner, name):
        self.private_name = "_" + name

    def __get__(self, obj, objtype=None):
        try:
            return getattr(obj, self.private_name)
        except AttributeError:
            raise AttributeError(self.error_message) from None

    def __set__(self, obj, value):
        setattr(obj, self.private_name, value)


class OneTimeSetter:
    def __set_name__(self, owner, name):
        self.private_name = f"__original_{name}"

    def __get__(self, obj, objtype=None):
        return getattr(obj, self.private_name)

    def __set__(self, obj, value):
        if hasattr(obj, self.private_name):
            raise ValueError("This attribute is frozen thus cannot mutate.")
        setattr(obj, self.private_name, value)


class ParamlessSingletonMeta(type):
    """Singleton implementation for class that does not require any parameter."""

    def __call__(cls):
        with suppress(AttributeError):
            return cls._instance

        cls._instance = super().__call__()
        return cls._instance
