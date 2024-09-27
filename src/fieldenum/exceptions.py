"""Exceptions used on this package."""

from typing import NoReturn as _NoReturn

_MISSING = object()


class FieldEnumError(Exception):
    pass


class Unreachable(BaseException):
    pass


def unreachable(value=_MISSING) -> _NoReturn:
    raise Unreachable(
        "This code is meant to be unreachable, but somehow the code reached here. "
        "Address developers to fix the issue." + f" Value: {value!r}" * (value is not _MISSING)
    )


class IncompatibleBoundError(FieldEnumError):
    pass
