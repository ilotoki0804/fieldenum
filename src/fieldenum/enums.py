# type: ignore
"""Collection of useful fieldenums.

WARNING: This submodule can only be imported on Python 3.12 or later.
"""

from __future__ import annotations

import functools
import sys
from typing import TYPE_CHECKING, Any, Callable, NoReturn, final, overload

from . import Unit, Variant, fieldenum, unreachable
from .exceptions import IncompatibleBoundError

__all__ = ["Option", "BoundResult", "Message", "Some", "Success", "Failed"]

_MISSING = object()


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

    @overload
    @classmethod
    def new(cls, value: None, /) -> Option[T]: ...

    @overload
    @classmethod
    def new[U](cls, value: Option[U] | U | None, /) -> Option[U]: ...

    @overload
    @classmethod
    def new(cls, value: Option[T] | T | None, /) -> Option[T]: ...

    @classmethod
    def new(cls, value, /):
        if isinstance(value, Option):
            return value

        match value:
            case None:
                return Option.Nothing

            case value:
                return Option.Some(value)

    @overload
    @classmethod
    def new_as_is(cls, value: None, /) -> Option[T]: ...

    @overload
    @classmethod
    def new_as_is[U](cls, value: U | None, /) -> Option[U]: ...

    @overload
    @classmethod
    def new_as_is(cls, value: T | None, /) -> Option[T]: ...

    @classmethod
    def new_as_is(cls, value: T | None, /) -> Option[T]:
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

    def map[U](self, func: Callable[[T], Option[U] | None | U], /) -> Option[U]:
        match self:
            case Option.Nothing:
                return Option.Nothing

            case Option.Some(value):
                return Option.new(func(value))

            case other:
                unreachable(other)

    def map_as_is[U](self, func: Callable[[T], U | None], /) -> Option[U]:
        match self:
            case Option.Nothing:
                return Option.Nothing

            case Option.Some(value):
                return Option.new_as_is(func(value))

            case other:
                unreachable(other)

    @classmethod
    def wrap[**Params, Return](cls, func: Callable[Params, Option[Return] | Return | None], /) -> Callable[Params, Option[Return]]:
        @functools.wraps(func)
        def decorator(*args: Params.args, **kwargs: Params.kwargs):
            return Option.new(func(*args, **kwargs))
        return decorator

    @classmethod
    def wrap_as_is[**Params, Return](cls, func: Callable[Params, Return | None], /) -> Callable[Params, Option[Return]]:
        @functools.wraps(func)
        def decorator(*args: Params.args, **kwargs: Params.kwargs):
            return Option.new_as_is(func(*args, **kwargs))
        return decorator


@final  # A redundant decorator for type checkers.
@fieldenum
class BoundResult[R, E: BaseException]:
    if TYPE_CHECKING:
        class Success[R, E](BoundResult[R, E]):
            __match_args__ = ("value", "bound")
            __fields__ = ("value", "bound")

            @property
            def value(self) -> R: ...

            @property
            def bound(self) -> type[E]: ...

            def __init__(self, value: R, bound: type[E]): ...

            def dump(self) -> tuple[R, E]: ...

        class Failed[R, E](BoundResult[R, E]):
            __match_args__ = ("error", "bound")
            __fields__ = ("error", "bound")

            @property
            def error(self) -> E: ...

            @property
            def bound(self) -> type[E]: ...

            def __init__(self, error: E, bound: type[E]): ...

            def dump(self) -> tuple[E, type[E]]: ...

        @property
        def bound(self) -> type[E]: ...

    else:
        Success = Variant(value=R, bound=type[E])
        Failed = Variant(error=E, bound=type[E])

    def __bool__(self) -> bool:
        return isinstance(self, BoundResult.Success)

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
        sys.exit(error_code if self else 0)

    def rebound[NewBound: BaseException](self, bound: type[NewBound], /) -> BoundResult[R, NewBound]:
        match self:
            case BoundResult.Success(value, _):
                return BoundResult.Success(value, bound)

            case BoundResult.Failed(error, _):
                return BoundResult.Failed(error, bound)

            case other:
                unreachable(other)

    def map[NewReturn](self, func: Callable[[R], BoundResult[NewReturn, Any] | NewReturn], /) -> BoundResult[NewReturn, E]:
        match self:
            case BoundResult.Success(ok, bound):
                try:
                    result = func(ok)
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

        match result:
            case BoundResult.Success(ok, _):
                return BoundResult.Success(ok, bound)

            case BoundResult.Failed(error, _):
                return BoundResult.Failed(error, bound)

            case other:
                return BoundResult.Success(other, bound)

    def map_as_is[NewReturn](self, func: Callable[[R], NewReturn], /) -> BoundResult[NewReturn, E]:
        match self:
            case BoundResult.Success(ok, bound):
                try:
                    return BoundResult.Success(func(ok), bound)

                except BaseException as error:
                    if isinstance(error, bound):
                        return BoundResult.Failed(error, bound)
                    else:
                        raise

            case BoundResult.Failed(_, _) as failed:
                return failed

            case other:
                unreachable(other)

    @overload
    @classmethod
    def wrap[**Params, Return, Bound: BaseException](
        cls, bound: type[Bound], /
    ) -> Callable[[Callable[Params, BoundResult[Return, Any] | Return]], Callable[Params, BoundResult[Return, Bound]]]: ...

    @overload
    @classmethod
    def wrap[**Params, Return, Bound: BaseException](
        cls, func: Callable[Params, BoundResult[Return, Any] | Return], bound: type[Bound], /
    ) -> Callable[Params, BoundResult[Return, Bound]]: ...

    @classmethod
    def wrap(cls, *args):
        match args:
            case (bound,):
                def decorator(func):
                    @functools.wraps(func)
                    def inner(*args, **kwargs):
                        try:
                            result = func(*args, **kwargs)
                        except BaseException as error:
                            if isinstance(error, bound):
                                return BoundResult.Failed(error, bound)
                            else:
                                raise

                        match result:
                            case BoundResult.Failed(error, _):
                                # basically same as rebound operation
                                return BoundResult.Failed(error, bound)

                            case BoundResult.Success(value, _):
                                return BoundResult.Success(value, bound)

                            case value:
                                return BoundResult.Success(value, bound)

                    return inner

                return decorator

            case func, bound:
                @functools.wraps(func)
                def inner(*args, **kwargs):
                    try:
                        result = BoundResult.Success(func(*args, **kwargs), bound)
                    except BaseException as error:
                        if isinstance(error, bound):
                            return BoundResult.Failed(error, bound)
                        else:
                            raise

                    match result:
                        case BoundResult.Failed(error, _):
                            # basically same as rebound operation
                            return BoundResult.Failed(error, bound)

                        case BoundResult.Success(value, _):
                            return BoundResult.Success(value, bound)

                        case value:
                            return BoundResult.Success(value, bound)

                return inner

            case _, _, *params:
                raise TypeError(f"Received unexpected parameter(s): {params}")

            case other:
                unreachable(other)

    @overload
    @classmethod
    def wrap_as_is[**Params, Return, Bound: BaseException](
        cls, bound: type[Bound], /
    ) -> Callable[[Callable[Params, Return]], Callable[Params, BoundResult[Return, Bound]]]: ...

    @overload
    @classmethod
    def wrap_as_is[**Params, Return, Bound: BaseException](
        cls, func: Callable[Params, Return], bound: type[Bound], /
    ) -> Callable[Params, BoundResult[Return, Bound]]: ...

    @classmethod
    def wrap_as_is(cls, *args):
        match args:
            case (bound,):
                def decorator(func):
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

                return decorator

            case func, bound:
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
