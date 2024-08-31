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


def test_tuple_variant():
    from fieldenum import Variant, Unit, fieldenum, unreachable

    @fieldenum
    class Message[T]:
        Quit = Variant(int)  # Variant(...)와 같이 적고 안에는 타입을 적습니다.
        Stay = Variant(T)  # 제너릭도 사용 가능합니다.
        Var3 = Variant(int, str, dict[int, str])  # 여러 값을 이어서 적으면 각각이 파라미터가 됩니다.

    Message.Quit(123)  # OK
    Message[str].Stay("hello")  # OK
    Message.Stay("hello")  # OK
    Message.Var3(123, "hello", {1: "world"})  # OK


def test_named_variant():
    from fieldenum import Variant, Unit, fieldenum, unreachable

    @fieldenum
    class Cord:
        D1 = Variant(x=float)
        D2 = Variant(x=float, y=float)
        D3 = Variant(x=float, y=float, z=float)
        D4 = Variant(timestamp=float, x=float, y=float, z=float)

    Cord.D1(x=123.456)
    Cord.D3(x=1343.5, y=25.2, z=465.312)

    Cord.D1(123.456)  # 가능
    Cord.D2(123.456, y=789.0)  # 가능
    Cord.D3(1.2, 2.3, 3.4)  # 가능

    cord = Cord.D3(x=1343.5, y=25.2, z=465.312)

    assert cord.x == 1343.5
    assert cord.y == 25.2
    assert cord.z == 465.312

    match cord:
        case Cord.D1(x=x):
            assert False

        case Cord.D2(x=x, y=y):
            assert False

        case Cord.D3(x=x, y=y, z=_):
            assert True

        case Cord.D3(timestamp=time, x=x, y=y, z=_):
            assert False


def test_kw_only():
    from fieldenum import Variant, Unit, fieldenum, unreachable

    @fieldenum
    class Cord:
        D1 = Variant(x=float).kw_only()
        D2 = Variant(x=float, y=float).kw_only()
        D3 = Variant(x=float, y=float, z=float).kw_only()
        D4 = Variant(timestamp=float, x=float, y=float, z=float).kw_only()

    Cord.D3(x=1343.5, y=25.2, z=465.312)
    with pytest.raises(TypeError):
        Cord.D1(123.456)  # XXX: 불가능
    with pytest.raises(TypeError):
        Cord.D2(123.456, y=789.0)  # XXX: 불가능
    with pytest.raises(TypeError):
        Cord.D3(1.2, 2.3, 3.4)  # XXX: 불가능


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
