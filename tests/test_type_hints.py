import pytest
from fieldenum import fieldenum, Variant, Unit
from fieldenum.enums import Option, BoundResult, Message, Some, Success, Failed
from typing import TYPE_CHECKING, assert_type


def test_option():
    option = Option.new("hello")
    assert_type(option, Option[str])

    # option = Option.Some("hello")
    # assert_type(option, Option[str])

    option = Option.new(None)
    assert_type(option, Option)

    option = Option[str].new(None)
    assert_type(option, Option[str])

    option = Option.new(Option.new("hello"))
    assert_type(option, Option[Option[str]])

    option = Option.new(Option.Nothing)
    assert_type(option, Option[Option])

    option = Option[str].Nothing
    assert_type(option, Option[str])

    option = Option.Some("hello")
    assert_type(option.unwrap(), str)

    if TYPE_CHECKING:
        option3: Option[str] = Option.Nothing
        assert_type(option3.unwrap(), str)

    option = Option.Some("hello")
    assert_type(option.unwrap("hi"), str)

    option = Option.Some("hello")
    assert_type(option.unwrap(123), str | int)

    if TYPE_CHECKING:
        option5: Option[str] = Option.Nothing
        assert_type(option5.expect("Cannot be None."), str)

        option4: Option[str] = Option.Nothing
        assert_type(option4.expect(TypeError("Cannot be None.")), str)

    option = Option.Some("hello")
    assert_type(option.map(lambda x: x + ", world!"), Option[str])

    option = Option.Some("hello")
    assert_type(option.map(lambda x: x + ", world!"), Option[str])

    option6: Option[str] = Option.Nothing
    assert_type(option6.map(lambda x: x + ", world!"), Option[str])

    option = Option.Some("hello")
    assert_type(option6.map(lambda _: 1), Option[int])

    option = Option.Some("hello")
    assert_type(option6.map(lambda _: Option.new(1)), Option[Option[int]])

    option = Option.Some("hello")
    assert_type(option6.map(lambda _: Option[int].Nothing), Option[Option[int]])

    @Option.wrap
    def wrapped[T](a: T) -> T | None:
        return a

    assert_type(wrapped(1), Option[int])
    # assert_type(wrapped(None), Option)  # not working and not needing to work

    @Option.wrap
    def wrapped2[T](a: T | None) -> Option[T]:
        return Option.new(a)

    assert_type(wrapped2(1), Option[Option[int]])


def test_fieldenum():
    with pytest.raises(TypeError):
        @fieldenum
        class FieldEnum:
            variant0 = Variant()
            variant1 = Variant(int)
            variant3 = Variant(named=str)
            # should raise type checker error
            variant3 = Variant(int, named=str)  # type: ignore
