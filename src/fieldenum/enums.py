# type: ignore
"""Collection of useful fieldenums.

WARNING: This submodule can only be imported on Python 3.12 or later.
"""

from __future__ import annotations

import functools
import sys
from typing import TYPE_CHECKING, Any, Callable, Mapping, NoReturn, Self, Sequence, final, overload, SupportsIndex

from . import Unit, Variant, fieldenum, unreachable
from .exceptions import IncompatibleBoundError, UnwrapFailedError

__all__ = ["Option", "BoundResult", "Message", "Some", "Success", "Failed"]

_MISSING = object()
type _ExceptionTypes = type[BaseException] | tuple[type[BaseException], ... ]
type _Types = type | tuple[type, ... ]


@final  # A redundant decorator for type checkers.
@fieldenum
class Option[T]:
    if TYPE_CHECKING:
        Nothing = Unit
        class Some[T](Option[T]):
            __match_args__ = ("_0",)
            __fields__ = (0,)

            @property
            def _0(self) -> T: ...

            def __init__(self, value: T, /): ...

            def dump(self) -> tuple[T]: ...

    else:
        Nothing = Unit
        Some = Variant(T)

    def __bool__(self):
        return self is not Option.Nothing

    @classmethod
    @overload
    def new(cls, value: None, /) -> Self: ...

    @classmethod
    @overload
    def new[U](cls, value: U | None, /) -> Option[U]: ...

    @classmethod
    def new(cls, value, /):
        match value:
            case None:
                return Option.Nothing

            case value:
                return Option.Some(value)

    @overload
    def unwrap(self) -> T: ...

    @overload
    def unwrap(self, default: T) -> T: ...

    @overload
    def unwrap[U](self, default: U) -> T | U: ...

    def unwrap(self, default=_MISSING):
        match self:
            case Option.Nothing if default is _MISSING:
                raise UnwrapFailedError("Unwrap failed.")

            case Option.Nothing:
                return default

            case Option.Some(value):
                return value

            case other:
                unreachable(other)

    def expect(self, message_or_exception: str | BaseException, /) -> T:
        match self, message_or_exception:
            case Option.Nothing, BaseException() as exception:
                raise exception

            case Option.Nothing, message:
                raise UnwrapFailedError(message)

            case Option.Some(value), _:
                return value

            case other:
                unreachable(other)

    # with defaults

    @overload
    def get[Key, Result, Default](
        self: Option[Mapping[Key, Result]],
        key: Key,
        *,
        default: Default,
        exc: _ExceptionTypes = ...,
        ignored: _Types = ...,
    ) -> Option[Result | Default]: ...

    @overload
    def get[Result, Default](
        self: Option[Sequence[Result]],
        key: SupportsIndex,
        *,
        default: Default,
        exc: _ExceptionTypes = ...,
        ignored: _Types = ...,
    ) -> Option[Result | Default]: ...

    # no default

    @overload
    def get[Key, Result](
        self: Option[Mapping[Key, Result]],
        key: Key,
        *,
        exc: _ExceptionTypes = ...,
        ignored: _Types = ...,
    ) -> Option[Result]: ...

    @overload
    def get[Result](
        self: Option[Sequence[Result]],
        key: SupportsIndex,
        *,
        exc: _ExceptionTypes = ...,
        ignored: _Types = ...,
    ) -> Option[Result]: ...

    # fallback

    @overload
    def get[Default](
        self,
        key,
        *,
        default: Default,
        exc: _ExceptionTypes = ...,
        ignored: _Types = ...,
    ) -> Option[Any | Default]: ...

    @overload
    def get(
        self,
        key,
        *,
        exc: _ExceptionTypes = ...,
        ignored: _Types = ...,
    ) -> Option: ...

    def get(self, key, *, default=_MISSING, exc=(TypeError, IndexError, KeyError), ignored=(str, bytes, bytearray)):
        match self:
            case Option.Nothing:
                return self

            case Option.Some(to_subscript):
                if ignored and isinstance(to_subscript, ignored):
                    return Option.Nothing.setdefault(default)
                try:
                    return Option.Some(to_subscript[key])
                except BaseException as e:
                    if not isinstance(e, exc):
                        raise
                    return Option.Nothing.setdefault(default)

    @overload
    def setdefault(self, value: T, /) -> Self: ...

    @overload
    def setdefault[U](self, value: U, /) -> Option[T | U]: ...

    def setdefault[U](self, value: U, /) -> Option[T | U]:
        if value is _MISSING:
            return self
        elif self is Option.Nothing:
            return Option.Some(value)
        else:
            return self

    def map[U](self, func: Callable[[T], U], /) -> Option[U]:
        match self:
            case Option.Nothing:
                return Option.Nothing

            case Option.Some(value):
                return Option.Some(func(value))

            case other:
                unreachable(other)

    @classmethod
    def wrap[**Params, Return](cls, func: Callable[Params, Return | None], /) -> Callable[Params, Option[Return]]:
        @functools.wraps(func)
        def decorator(*args: Params.args, **kwargs: Params.kwargs):
            return Option.new(func(*args, **kwargs))
        return decorator


@final  # A redundant decorator for type checkers.
@fieldenum
class BoundResult[R, E: BaseException]:
    if TYPE_CHECKING:
        class Success[R, E: BaseException](BoundResult[R, E]):
            __match_args__ = ("value", "bound")
            __fields__ = ("value", "bound")

            @property
            def value(self) -> R: ...

            @property
            def bound(self) -> type[E]: ...

            def __init__(self, value: R, bound: type[E]): ...

            def dump(self) -> tuple[R, E]: ...

        class Failed[R, E: BaseException](BoundResult[R, E]):
            __match_args__ = ("error", "bound")
            __fields__ = ("error", "bound")

            @property
            def error(self) -> E: ...

            @property
            def bound(self) -> type[E]: ...

            def __init__(self, error: BaseException, bound: type[E]): ...

            def dump(self) -> tuple[E, type[E]]: ...

        @property
        def bound(self) -> type[E]: ...

    else:
        Success = Variant(value=R, bound=type[E])
        Failed = Variant(error=E, bound=type[E])

    def __bool__(self) -> bool:
        return isinstance(self, BoundResult.Success)

    if __debug__:
        def __post_init__(self):
            if not issubclass(self.bound, BaseException):
                raise IncompatibleBoundError(f"{self.bound} is not an exception.")

            if isinstance(self, Failed) and not isinstance(self.error, self.bound):
                raise IncompatibleBoundError(
                    f"Bound {self.bound.__qualname__!r} is not compatible with existing error: {type(self.error).__qualname__}."
                )

    @overload
    def unwrap(self) -> R: ...

    @overload
    def unwrap(self, default: R) -> R: ...

    @overload
    def unwrap[T](self, default: T) -> R | T: ...

    def unwrap(self, default=_MISSING):
        match self:
            case BoundResult.Success(value, _):
                return value

            case BoundResult.Failed(error, _) if default is _MISSING:
                raise error

            case BoundResult.Failed(error, _):
                return default

            case other:
                unreachable(other)

    def as_option(self) -> Option[R]:
        match self:
            case BoundResult.Success(value, _):
                return Option.Some(value)

            case BoundResult.Failed(_, _):
                return Option.Nothing

            case other:
                unreachable(other)

    def exit(self, error_code: str | int | None = 1) -> NoReturn:
        sys.exit(0 if self else error_code)

    def rebound[NewBound: BaseException](self, bound: type[NewBound], /) -> BoundResult[R, NewBound]:
        match self:
            case BoundResult.Success(value, _):
                return BoundResult.Success(value, bound)

            case BoundResult.Failed(error, _):
                return BoundResult.Failed(error, bound)

            case other:
                unreachable(other)

    def map[NewReturn](self, func: Callable[[R], NewReturn], /) -> BoundResult[NewReturn, E]:
        match self:
            case BoundResult.Success(ok, bound):
                try:
                    return BoundResult.Success(func(ok), bound)
                except BaseException as error:
                    if isinstance(error, bound):
                        return BoundResult.Failed(error, bound)
                    else:
                        raise

            case BoundResult.Failed(error, bound) as failed:
                if TYPE_CHECKING:
                    return BoundResult.Failed[NewReturn, E](error, bound)
                else:
                    return failed

            case other:
                unreachable(other)

    @overload
    @classmethod
    def wrap[**Params, Return, Bound: BaseException](
        cls, bound: type[Bound], /
    ) -> Callable[[Callable[Params, Return]], Callable[Params, BoundResult[Return, Bound]]]: ...

    @overload
    @classmethod
    def wrap[**Params, Return, Bound: BaseException](
        cls, bound: type[Bound], func: Callable[Params, Return], /
    ) -> Callable[Params, BoundResult[Return, Bound]]: ...

    @classmethod
    def wrap(cls, bound, func=None) -> Any:
        if func is None:
            return lambda func: cls.wrap(bound, func)

        @functools.wraps(func)
        def inner(*args, **kwargs):
            try:
                return BoundResult.Success(func(*args, **kwargs), bound)
            except BaseException as error:
                if isinstance(error, bound):
                    return BoundResult.Failed(error, bound)
                else:
                    raise
        return inner


@final  # A redundant decorator for type checkers.
@fieldenum
class Message:
    """Test fieldenum to play with."""
    if TYPE_CHECKING:
        Quit = Unit

        class Move(Message):
            __match_args__ = ("x", "y")
            __fields__ = ("x", "y")

            @property
            def x(self) -> int: ...

            @property
            def y(self) -> int: ...

            def __init__(self, x: int, y: int): ...

            def dump(self) -> dict[str, int]: ...

        class Write(Message):
            __match_args__ = ("_0",)
            __fields__ = (0,)

            @property
            def _0(self) -> str: ...

            def __init__(self, message: str, /): ...

            def dump(self) -> tuple[int]: ...

        class ChangeColor(Message):
            __match_args__ = ("_0", "_1", "_2")
            __fields__ = (0, 1, 2)

            @property
            def _0(self) -> int: ...

            @property
            def _1(self) -> int: ...

            @property
            def _2(self) -> int: ...

            def __init__(self, red: int, green: int, blue: int, /): ...

            def dump(self) -> tuple[int, int, int]: ...

        class Pause(Message):
            __match_args__ = ()
            __fields__ = ()

            @property
            def _0(self) -> int: ...

            @property
            def _1(self) -> int: ...

            @property
            def _2(self) -> int: ...

            def __init__(self): ...

            def dump(self) -> tuple[()]: ...

    else:
        Quit = Unit
        Move = Variant(x=int, y=int)
        Write = Variant(str)
        ChangeColor = Variant(int, int, int)
        Pause = Variant()


Some = Option.Some
Success = BoundResult.Success
Failed = BoundResult.Failed
