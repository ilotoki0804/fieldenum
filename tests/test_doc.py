# type: ignore
from __future__ import annotations

import pytest


def test_decorator():
    from fieldenum import Unit, Variant, fieldenum, unreachable

    @fieldenum
    class IpAddrKind:
        V4 = Unit
        V6 = Unit

    _ = IpAddrKind.V4
    _ = IpAddrKind.V6

    def route(ip_kind: IpAddrKind):
        pass

    route(IpAddrKind.V4)
    route(IpAddrKind.V6)


def test_unit_variant():
    from fieldenum import Unit, Variant, fieldenum, unreachable

    @fieldenum
    class Message:
        Quit = Unit
        Stay = Unit
        Fieldless = Variant()

    assert Message.Quit is not Message.Stay
    assert Message.Fieldless() is Message.Fieldless()
    message: Message = Message.Quit
    assert message is Message.Quit

    match message:
        case Message.Stay:
            assert False

        case Message.Fieldless():
            assert False

        case Message.Quit:
            assert True

        case other:
            unreachable(other)


def test_dataclasses():
    from dataclasses import dataclass

    from fieldenum import Unit, Variant, fieldenum, unreachable

    @fieldenum
    class IpAddrKind:
        V4 = Unit
        V6 = Unit

    @dataclass
    class IpAddr:
        kind: IpAddrKind
        address: str

    _ = IpAddr(kind=IpAddrKind.V4, address="127.0.0.1")
    _ = IpAddr(kind=IpAddrKind.V6, address="::1")


def test_fields():
    from fieldenum import Unit, Variant, fieldenum, unreachable

    @fieldenum
    class IpAddrKind:
        V4 = Variant(str)
        V6 = Variant(str)

    _ = IpAddrKind.V4("127.0.0.1")
    _ = IpAddrKind.V6("::1")

    @fieldenum
    class IpAddrKind:
        V4 = Variant(int, int, int, int)
        V6 = Variant(str)

    _ = IpAddrKind.V4(127, 0, 0, 1)
    _ = IpAddrKind.V6("::1")


def test_runtime():
    from fieldenum import Unit, Variant, fieldenum, unreachable

    @fieldenum(runtime_check=True)
    class Message[T]:
        # 일반 타입은 `isinstance()`를 통해 확인됩니다.
        Quit = Variant(int)
        # 제너릭은 검사되지 않습니다.
        Stay = Variant(T)
        # 각각의 파라미터에 타입을 체크합니다.
        # 이때 Union (이 경우 `str | int`)는 체크되지만
        # generic alias (이 경우`dict[int, str]`)는 체크되지 않습니다.
        Var3 = Variant(int, str | int, dict[int, str])

    Message.Quit(123)  # 오류 없음
    with pytest.raises(TypeError):
        Message.Quit("invalid")  # TypeError
    Message.Stay("hello")  # 오류 없음
    Message.Stay(1234)  # 잘못됐지만 오류 없음
    Message.Var3(123, "hello", {1: "world"})  # 오류 없음
    Message.Var3(123, 123, {1: "world"})  # 오류 없음
    with pytest.raises(TypeError):
        Message.Stay(123, 123.456, {1: "world"})  # TypeError
    Message.Var3(123, "hello", {"hello": "world"})  # 잘못됐지만 오류 없음
    Message.Var3(123, "hello", 123)  # 잘못됐지만 오류 없음


def test_list():
    from fieldenum import Unit, Variant, fieldenum, unreachable


    @fieldenum
    class List:
        Cons = Variant(int, "List")
        Nil = Unit

        @classmethod
        def new(cls) -> List:
            return List.Nil

        def prepend(self, elem: int) -> List:
            return List.Cons(elem, self)

        def __len__(self) -> int:
            match self:
                case List.Cons(_, tail):
                    return 1 + len(tail)

                case List.Nil:
                    return 0

                case other:
                    unreachable(other)

        def __str__(self) -> str:
            match self:
                case List.Cons(head, tail):
                    return f"{head}, {tail}"

                case List.Nil:
                    return "Nil"

                case other:
                    unreachable(other)


    linked_list = List.new()
    linked_list = linked_list.prepend(1)
    linked_list = linked_list.prepend(2)
    linked_list = linked_list.prepend(3)
    assert len(linked_list) == 3
    assert str(linked_list) == "3, 2, 1, Nil"


def test_unit():
    from fieldenum import Unit, Variant, fieldenum

    @fieldenum
    class NoFieldVariants:
        UnitVariant = Unit
        FieldlessVariant = Variant()

    unit = NoFieldVariants.UnitVariant  # 괄호를 필요로 하지 않습니다.
    fieldless = NoFieldVariants.FieldlessVariant()  # 괄호를 필요로 합니다.

    # 두 배리언트 모두 isinstance로 확인할 수 있습니다.
    assert isinstance(unit, NoFieldVariants)
    assert isinstance(fieldless, NoFieldVariants)

    # 두 배리언트 모두 싱글톤이기에 `is` 연산자로 동일성을 확인할 수 있습니다.
    assert unit is NoFieldVariants.UnitVariant
    assert fieldless is NoFieldVariants.FieldlessVariant()
