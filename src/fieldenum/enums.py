# type: ignore

from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any, Callable, Literal, Self, final, overload

from . import Unit, Variant, fieldenum, unreachable
from .exceptions import UnwrapFailedError

__all__ = ["Option", "BoundResult", "Message", "Some", "Success", "Failed"]

_MISSING = object()


@final  # a redundant decorator for type checkers
@fieldenum
class Option[T]:
    Nothing = Unit
    Some = Variant(T)

    @classmethod
    def new(cls, value: T | None | Self, as_is=False) -> Self:
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

    def unwrap(self, default: T = _MISSING) -> T:
        match self:
            case Option.Nothing if default is _MISSING:
                raise UnwrapFailedError("Unwrap failed.")

            case Option.Nothing:
                return default

            case Option.Some(value):
                return value

            case other:
                unreachable(other)

    def expect(self, value_or_error, /) -> T:
        match self:
            case Option.Nothing if isinstance(value_or_error, BaseException):
                raise value_or_error

            case Option.Nothing:
                raise UnwrapFailedError(value_or_error)

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


@final  # a redundant decorator for type checkers
@fieldenum
class BoundResult[R, E: BaseException]:
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

    def unwrap(self, default: R = _MISSING) -> R:
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

    def map[NewReturn](
        self, func: Callable[[R], BoundResult[NewReturn, Any] | NewReturn], /, *, as_is: bool = False
    ) -> BoundResult[NewReturn, E]:
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


@final  # a redundant decorator for type checkers
@fieldenum
class Message:
    """Test fieldenum to play with."""
    Quit = Unit
    Move = Variant(x=int, y=int)
    Write = Variant(str)
    ChangeColor = Variant(int, int, int)
    Pause = Variant()


if TYPE_CHECKING:
    class Some[T](Option[T]):
        __match_args__ = ("value",)

        def __init__(self, value: T, /): ...

    class Success[R, E](BoundResult[R, E]):
        __match_args__ = ("result", "bound")

        def __init__(self, result: R, bound: type[E], /): ...

    class Failed[R, E](BoundResult[R, E]):
        __match_args__ = ("result", "bound")

        def __init__(self, result: E, bound: type[E], /): ...

else:
    Some = Option.Some
    Success = BoundResult.Success
    Failed = BoundResult.Failed
