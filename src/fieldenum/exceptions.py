"""Exceptions used on this package."""

from typing import NoReturn as _NoReturn

_MISSING = object()


class FieldEnumError(Exception):
    pass


class UnreachableError(Exception):
    pass


def unreachable(value=_MISSING) -> _NoReturn:
    if value is _MISSING:
        raise UnreachableError(
            "This code is meant to be unreachable, but somehow the code reached here. "
            "Address developers to fix the issue."
        )
    else:
        raise UnreachableError(
            f"Unexpected type {type(value).__name__!r} of {value!r}"
        )


class UnwrapFailedError(FieldEnumError):
    pass


class IncompatibleBoundError(FieldEnumError):
    pass
