# type: ignore
"""Collection of useful fieldenums.

WARNING: This submodule can only be imported on Python 3.12 or later.
"""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any, Callable, Literal, Self, final, overload

from . import Unit, Variant, fieldenum, unreachable

__all__ = ["Option", "BoundResult", "Message", "Some", "Success", "Failed"]

_MISSING = object()


@final  # A redundant decorator for type checkers.
@fieldenum
class Option[T]:
    if TYPE_CHECKING:
        Nothing = Unit
        class Some[T](Option[T]):
            __match_args__ = ("_0",)
            __fields__ = ("_0",)

            @property
            def _0(self) -> T:
                ...

            def __init__(self, value: T, /): ...

            def dump(self) -> tuple[T]: ...

    else:
        Nothing = Unit
        Some = Variant(T)

    @overload
    @classmethod
    def new(cls, value: T | None, as_is: Literal[True]) -> Option[T]: ...

    @overload
    @classmethod
    def new(cls, value: T | None | Option[T], as_is: Literal[False] = ...) -> Option[T]: ...

    @classmethod
    def new(cls, value, as_is=False):
        if not as_is and isinstance(value, Option):
            return value

        match value:
            case None:
                return Option.Nothing

            case value:
                return Option.Some(value)

    @overload
    def unwrap(self) -> T: ...

    @overload
    def unwrap(self, default: T) -> T: ...

    def unwrap(self, default=_MISSING):
        match self:
            case Option.Nothing if default is _MISSING:
                raise ValueError("Unwrap failed.")

            case Option.Nothing:
                return default

            case Option.Some(value):
                return value

            case other:
                unreachable(other)

    def expect(self, message_or_exception: str | BaseException, /) -> T:
        match self:
            case Option.Nothing if isinstance(message_or_exception, BaseException):
                raise message_or_exception

            case Option.Nothing:
                raise ValueError(message_or_exception)

            case Option.Some(value):
                return value

            case other:
                unreachable(other)

    @overload
    def map[U](
        self,
        func: Callable[[T], Option[U] | U | None],
        /,
        *,
        as_is: Literal[False] = ...,
    ) -> Option[U]: ...

    @overload
    def map[U](
        self,
        func: Callable[[T], U | None],
        /,
        *,
        as_is: Literal[True] = ...,
    ) -> Option[U]: ...

    def map(self, func, /, *, as_is=False):
        if not self:
            return self

        result = func(self.unwrap())

        match result:
            case None:
                return Option.Nothing

            case result if as_is:
                return Option.Some(result)

            case Option.Nothing:
                return Option.Nothing

            case Option.Some(_) as result:
                return result

            case result:
                return Option.Some(result)

    def __bool__(self):
        return self is not Option.Nothing

    @classmethod
    def wrap[**Params, Return](cls, func: Callable[Params, Return | None], /) -> Callable[Params, Option[Return]]:
        @functools.wraps(func)
        def decorator(*args: Params.args, **kwargs: Params.kwargs) -> Option[Return]:
            return Option.new(func(*args, **kwargs))
        return decorator


@final  # A redundant decorator for type checkers.
@fieldenum
class BoundResult[R, E: BaseException]:
    if TYPE_CHECKING:
        class Success[R, E](BoundResult[R, E]):
            __match_args__ = ("_0", "_1")
            __fields__ = ("_0", "_1")

            @property
            def _0(self) -> R:
                ...

            @property
            def _1(self) -> type[E]:
                ...

            def __init__(self, result: R, bound: type[E], /): ...

            def dump(self) -> tuple[R, E]: ...

        class Failed[R, E](BoundResult[R, E]):
            __match_args__ = ("_0", "_1")
            __fields__ = ("_0", "_1")

            @property
            def _0(self) -> R:
                ...

            @property
            def _1(self) -> type[E]:
                ...

            def __init__(self, result: E, bound: type[E], /): ...

            def dump(self) -> tuple[R, E]: ...

    else:
        Success = Variant(R, type[E])
        Failed = Variant(E, type[E])

    @property
    def bound(self) -> type[E]:
        match self:
            case BoundResult.Success(_, bound):
                return bound

            case BoundResult.Failed(_, bound):
                return bound

            case other:
                unreachable(other)

    @overload
    def unwrap(self) -> R: ...

    @overload
    def unwrap(self, default: R) -> R: ...

    def unwrap(self, default=_MISSING):
        match self:
            case BoundResult.Success(ok, _):
                return ok

            case BoundResult.Failed(err, _) if default is _MISSING:
                raise err

            case BoundResult.Failed(err, _):
                return default

            case other:
                unreachable(other)

    def as_option(self) -> Option[R]:
        match self:
            case BoundResult.Success(ok, _):
                return Option.Some(ok)

            case BoundResult.Failed(_, _):
                return Option.Nothing

            case other:
                unreachable(other)

    def rebound[NewBound: BaseException](self, bound: type[NewBound], /) -> BoundResult[R, NewBound]:
        match self:
            case BoundResult.Success(ok, _):
                return BoundResult.Success(ok, bound)

            case BoundResult.Failed(err, _):
                return BoundResult.Failed(err, bound)

            case other:
                unreachable(other)

    def __bool__(self) -> bool:
        match self:
            case BoundResult.Success(_, _):
                return True

            case BoundResult.Failed(_, _):
                return False

            case other:
                unreachable(other)

    @overload
    def map[NewReturn](
        self, func: Callable[[R], NewReturn], /, *, as_is: Literal[True]
    ) -> BoundResult[NewReturn, E]: ...

    @overload
    def map[NewReturn](
        self, func: Callable[[R], BoundResult[NewReturn, Any] | NewReturn], /, *, as_is: Literal[False] = ...
    ) -> BoundResult[NewReturn, E]: ...

    def map(self, func, /, *, as_is=False):
        match self:
            case BoundResult.Success(ok, bound):
                try:
                    if as_is:
                        return BoundResult.Success(func(ok), bound)

                    result = func(ok)
                except bound as exc:
                    return BoundResult.Failed(exc, bound)

            case BoundResult.Failed(_, _) as failed:
                return failed

            case other:
                unreachable(other)

        match result:
            case BoundResult.Success(ok, _):
                return BoundResult.Success(ok, bound)

            case BoundResult.Failed(err, _):
                return BoundResult.Failed(err, bound)

            case other:
                return BoundResult.Success(other, bound)

    @overload
    @classmethod
    def wrap[**Params, Return, Bound: BaseException](
        cls, bound: type[Bound], /
    ) -> Callable[[Callable[Params, Return]], Callable[Params, BoundResult[Return, Bound]]]: ...

    @overload
    @classmethod
    def wrap[**Params, Return, Bound: BaseException](
        cls, func: Callable[Params, Return], bound: type[Bound], /
    ) -> Callable[Params, BoundResult[Return, Bound]]: ...

    @classmethod
    def wrap(cls, *args):
        match args:
            case [bound]:
                def decorator(func):
                    @functools.wraps(func)
                    def inner(*args, **kwargs):
                        try:
                            return BoundResult.Success(func(*args, **kwargs), bound)
                        except bound as exc:
                            return BoundResult.Failed(exc, bound)

                    return inner

                return decorator

            case func, bound:
                @functools.wraps(func)
                def inner(*args, **kwargs):
                    try:
                        return BoundResult.Success(func(*args, **kwargs), bound)
                    except bound as exc:
                        return BoundResult.Failed(exc, bound)

                return inner

            case _, _, *params:
                raise TypeError(f"Received unexpected parameter(s): {params}")

            case other:
                unreachable(other)


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
            def x(self) -> int:
                ...

            @property
            def y(self) -> int:
                ...

            def __init__(self, x: int, y: int): ...

            def dump(self) -> dict[str, int]: ...

        class Write(Message):
            __match_args__ = ("_0",)
            __fields__ = ("_0",)

            @property
            def _0(self) -> str:
                ...

            def __init__(self, message: str, /): ...

            def dump(self) -> tuple[int]: ...

        class ChangeColor(Message):
            __match_args__ = ("_0", "_1", "_2")
            __fields__ = ("_0", "_1", "_2")

            @property
            def _0(self) -> int:
                ...

            @property
            def _1(self) -> int:
                ...

            @property
            def _2(self) -> int:
                ...

            def __init__(self, red: int, green: int, blue: int, /): ...

            def dump(self) -> tuple[int, int, int]: ...

        class Pause(Message):
            __match_args__ = ()
            __fields__ = ()

            @property
            def _0(self) -> int:
                ...

            @property
            def _1(self) -> int:
                ...

            @property
            def _2(self) -> int:
                ...

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
