# type: ignore

import pickle
from typing import Any, Self

import pytest
from fieldenum import Unit, Variant, factory, fieldenum, unreachable, variant
from fieldenum.exceptions import UnreachableError


class ExceptionForTest(Exception):
    def __init__(self, value):
        self.value = value


@fieldenum
class Message:
    Quit = Unit
    Move = Variant(x=int, y=int).kw_only().default(x=234569834)
    ArgMove = Variant(x=int, y=int).default(x=234569834)
    FactoryTest = Variant(x=int, y=list, z=dict).default(y=factory(list), z=factory(lambda: {"hello": "world"}))
    Write = Variant(str)
    ChangeColor = Variant(int, int, int)
    Pause = Variant()

    @variant
    class ClassVariant:
        x: int
        y: "Message"
        z: str = "hello"

    @variant(kw_only=True)
    class KwOnlyClassVariant:
        x: int
        y: "Message"
        z: str = "hello"

    @variant
    def FunctionVariantWithBody(self, a: int, b, /, c: str, d, *, f: float = 3.4, e: dict | None = None, raise_it: bool = False):
        if raise_it:
            raise ExceptionForTest((self, a, b, c, d, f, e))

    @variant
    def FunctionVariant(a: int, b, /, c: str, d, *, f: float = factory(float), e: dict | None = factory(lambda: {"hello": "good"})):
        raise ExceptionForTest((a, b, c, d, f, e))

    @variant
    def NotNoneReturnFunctionVariant(self, a: int, b, /, c: str, d, *, f: float = factory(float), e: dict | None = factory(lambda: {"hello": "good"})):
        return 123

    @variant
    def ArgsOnlyFuncVariant(a, b, /, c, d):
        pass

    @variant
    def KwargsOnlyFuncVariant(*, a, b, c, d=None):
        pass

    @variant
    def ParamlessFuncVariantWithBody(self):
        pass


def test_unreachable():
    with pytest.raises(UnreachableError, match="Unexpected type 'str' of 'hello'"):
        unreachable("hello")
    with pytest.raises(UnreachableError, match="This code is meant to be unreachable, but somehow the code reached here. Address developers to fix the issue."):
        unreachable()

def test_class_variant():
    variant = Message.ClassVariant(123, Message.Quit)
    assert variant.dump() == dict(x=123, y=Message.Quit, z="hello")

    variant = Message.ClassVariant(123, y=Message.ArgMove(y=34))
    assert variant.dump() == dict(x=123, y=Message.ArgMove(x=234569834, y=34), z="hello")

    variant = Message.KwOnlyClassVariant(x=123, y=Message.ArgMove(y=34))
    assert variant.dump() == dict(x=123, y=Message.ArgMove(x=234569834, y=34), z="hello")

    with pytest.raises(TypeError):
        Message.KwOnlyClassVariant(123, y=Message.ArgMove(y=34))

    with pytest.raises(TypeError):
        Message.KwOnlyClassVariant(123, Message.ArgMove(y=34))


def test_default_factory():
    message = Message.FactoryTest(x=234, y=[12, 3], z={})
    assert message.dump() == dict(x=234, y=[12, 3], z={})

    message = Message.FactoryTest(x=456)
    assert message.dump() == dict(x=456, y=[], z={"hello": "world"})


def test_none_kw_only():
    assert Message.ArgMove(1, 2) == Message.ArgMove(1, y=2) == Message.ArgMove(x=1, y=2)
    with pytest.raises(TypeError):
        Message.ArgMove(1, 2, 3)
    with pytest.raises(TypeError):
        Message.ArgMove(1, 2, x=1)
    with pytest.raises(TypeError):
        Message.ArgMove(1, 2, x=1)
    with pytest.raises(TypeError):
        Message.ArgMove(1, x=1)
    assert Message.ArgMove(234569834, 234) == Message.ArgMove(y=234)


def test_misc():
    with pytest.raises(TypeError):
        Message()

    with pytest.raises(TypeError):
        @fieldenum
        class DerivedMessage(Message):
            New = Unit

    with pytest.raises(TypeError):
        @fieldenum
        class Mixed:
            New = Variant(str, x=int)

    with pytest.raises(TypeError, match="self.name"):
        Unit.attach(Message, eq=True, build_hash=False, build_repr=False, frozen=False)

    with pytest.raises(TypeError):
        message = Message.Move(x=123, y=567)
        message.x = 224

    assert Message.Move(y=325) == Message.Move(x=234569834, y=325)

    with pytest.raises(TypeError):
        @fieldenum
        class TupleDefault:
            Move = Variant(int, int).default(a=123)

    with pytest.raises(TypeError):
        @fieldenum
        class FieldlessDefault:
            Move = Variant().default(a=123)


def test_mutable_fieldenum():
    @fieldenum(frozen=False)
    class Message:
        Quit = Unit
        Move = Variant(x=int, y=int).kw_only()
        Write = Variant(str)
        ChangeColor = Variant(int, int, int)
        Pause = Variant()

        @variant
        def FunctionVariantWithBody(self, a: int, b, /, c: str, d, *, f: float = 3.4, e: dict | None = None, raise_it: bool = False):
            if raise_it:
                raise ExceptionForTest((self, a, b, c, d, f, e))

    with pytest.raises(TypeError, match="unhashable type:"):
        {Message.Quit}

    with pytest.raises(TypeError, match="unhashable type:"):
        {Message.Move(x=123, y=345)}

    with pytest.raises(TypeError, match="unhashable type:"):
        {Message.Write("hello")}

    with pytest.raises(TypeError, match="unhashable type:"):
        {Message.ChangeColor(123, 456, 789)}

    with pytest.raises(TypeError, match="unhashable type:"):
        {Message.Pause()}

    with pytest.raises(TypeError, match="unhashable type:"):
        {Message.FunctionVariantWithBody(1, 2, "hello", d=123, f=1.3, e={"hello": "world"})}

    message = Message.Move(x=123, y=345)
    message.x = 654
    assert message == Message.Move(x=654, y=345)
    assert message.dump() == {"x": 654, "y": 345}

    message = Message.Write("hello")
    message._0 = "world"
    assert message == Message.Write("world")
    assert message.dump() == ("world",)

    message = Message.ChangeColor(123, 456, 789)
    message._1 = 2345
    assert message == Message.ChangeColor(123, 2345, 789)
    assert message.dump() == (123, 2345, 789)

    assert Message.Quit.dump() is None
    assert Message.Pause().dump() == ()

    message = Message.FunctionVariantWithBody(1, 2, "hello", d=123, f=1.3, e={"hello": "world"})
    message.a = 235
    message.e = [235, 346]
    assert message.dump() == dict(a=235, b=2, c="hello", d=123, f=1.3, e=[235, 346], raise_it=False)


def test_relationship():
    # Unit variants are the instances. Use fieldless variant if you want issubclass work.
    # Theoretically it's possible to make it to be both subclass and instance of original class,
    # It breaks instance and class methods.
    assert isinstance(Message.Quit, Message)

    assert issubclass(Message.Move, Message)
    assert isinstance(Message.Write("hello"), Message.Write)
    assert isinstance(Message.Write("hello"), Message)
    assert isinstance(Message.Move(x=123, y="hello"), Message.Move)
    assert isinstance(Message.Move(x=123, y="hello"), Message)
    assert isinstance(Message.ChangeColor(123, 456, 789), Message.ChangeColor)
    assert isinstance(Message.ChangeColor(123, 456, 789), Message)
    assert isinstance(Message.Pause(), Message.Pause)
    assert isinstance(Message.Pause(), Message)


def test_instancing():
    type MyTypeAlias = int | str | bytes

    @fieldenum
    class Message[T]:
        Quit = Unit
        Move = Variant(x=int, y=int).kw_only()
        Write = Variant(str)
        ChangeColor = Variant(int | str, T, Any)
        Pause = Variant()
        UseTypeAlias = Variant(MyTypeAlias)
        UseSelf = Variant(Self)

    Message.Move(x=123, y=567)
    Message.Write("hello, world!")
    Message.ChangeColor("hello", (), 123)
    Message.ChangeColor(1234, [], b"bytes")
    Message.Pause()

    with pytest.raises(TypeError, match=r"Expect 3 field\(s\), but received 4 argument\(s\)\."):
        Message.ChangeColor(1, 2, 3, 4)

    with pytest.raises(TypeError, match=r"Expect 3 field\(s\), but received 4 argument\(s\)\."):
        Message.ChangeColor(1, 2, 3, 4)

    with pytest.raises(TypeError, match="x"):
        Message.Move(y=4)

    with pytest.raises(TypeError, match="hello"):
        Message.Move(hello=4)


def test_eq_and_hash():
    assert Message.ChangeColor(1, ("hello",), [1, 2, 3]) == Message.ChangeColor(1, ("hello",), [1, 2, 3])
    assert Message.FunctionVariant(1, 2, "hello", d=123, f=1.3, e={"hello": "world"}) == Message.FunctionVariant(
        1, 2, "hello", d=123, f=1.3, e={"hello": "world"})
    my_set = {
        Message.ChangeColor(1, ("hello",), (1, 2, 3)),
        Message.Quit,
        Message.Move(x=234, y=(2, "hello")),
        Message.Pause(),
        Message.FunctionVariant(1, 2, "hello", d=123, f=1.3, e="world")
    }
    assert Message.ChangeColor(1, ("hello",), (1, 2, 3)) in my_set
    assert Message.Quit in my_set
    assert Message.Move(x=234, y=(2, "hello")) in my_set
    assert Message.Pause() in my_set
    assert Message.FunctionVariant(1, 2, "hello", d=123, f=1.3, e="world") in my_set

    my_set.add(Message.ChangeColor(1, ("hello",), (1, 2, 3)))
    my_set.add(Message.Quit)
    my_set.add(Message.Move(x=234, y=(2, "hello")))
    my_set.add(Message.Pause())
    my_set.add(Message.FunctionVariant(1, 2, "hello", d=123, f=1.3, e="world"))
    assert len(my_set) == 5


@pytest.mark.parametrize(
    "message",
    [
        Message.Move(x=123, y=456),
        Message.ChangeColor(1, 2, 3),
        Message.Pause(),
        Message.Write("hello"),
        Message.Quit,
        Message.FunctionVariant(1, 2, "hello", d=123, f=1.3, e={"hello": "world"}),
    ],
)
def test_pickling(message):
    dump = pickle.dumps(message)
    load = pickle.loads(dump)
    assert message == load


def test_complex_matching():
    match Message.Move(x=123, y=456):
        case Message.Write("hello"):
            assert False

        case Message.Move(x=_, y=123):
            assert False

        case Message.Move(x=_, y=1 | 456):
            assert True

        case other:
            assert False, other


@pytest.mark.parametrize(
    "message,expect",
    [
        (Message.Move(x=123, y=456), ("move", 456)),
        (Message.ChangeColor(1, 2, 3), ("color", 1, 2, 3)),
        (Message.Pause(), "fieldless"),
        (Message.Write("hello"), ("write", "hello")),
        (Message.Quit, "quit"),
        (Message.FunctionVariant(1, 2, "hello", d=123, f=1.3, e={"hello": "world"}), "function_variant"),
    ],
)
def test_simple_matching(message, expect):
    match message:
        case Message.ChangeColor(x, y, z):
            assert expect == ("color", x, y, z)

        case Message.Quit:
            assert expect == "quit"

        case Message.Pause():
            assert expect == "fieldless"

        case Message.Write(msg):
            assert expect == ("write", msg)

        case Message.Move(x=123, y=y):
            assert expect == ("move", y)

        case Message.FunctionVariant(1, 2, "hello", d=123, f=1.3, e={"hello": "world"}):
            assert expect == "function_variant"

    # don't do these
    match message:
        case Message.ChangeColor(x, y):
            assert expect[0] == "color"

        case Message.Write():
            assert expect[0] == "write"

        case Message.Move():
            assert expect[0] == "move"


def test_repr():
    assert repr(Message.Quit) == "Message.Quit"
    assert repr(Message.Move(x=123, y=234)) == "Message.Move(x=123, y=234)"
    assert repr(Message.Write("hello!")) == "Message.Write('hello!')"
    assert repr(Message.ChangeColor(123, 456, 789)) == "Message.ChangeColor(123, 456, 789)"
    assert repr(Message.Pause()) == "Message.Pause()"
    assert repr(Message.FunctionVariant(1, 2, "hello", d=123, f=1.3, e={"hello": "world"})) == "Message.FunctionVariant(1, 2, 'hello', 123, f=1.3, e={'hello': 'world'})"
    assert repr(Message.ArgsOnlyFuncVariant(1,2,3,d=4)) == "Message.ArgsOnlyFuncVariant(1, 2, 3, 4)"
    assert repr(Message.KwargsOnlyFuncVariant(a=1,b=2,c=3)) == "Message.KwargsOnlyFuncVariant(a=1, b=2, c=3, d=None)"
    assert repr(Message.ParamlessFuncVariantWithBody()) == "Message.ParamlessFuncVariantWithBody()"

    assert repr(Message.Quit) == "Message.Quit"
    assert repr(Message.Move) == "<class 'fieldenum._fieldenum.Message.Move'>"
    assert repr(Message.Write) == "<class 'fieldenum._fieldenum.Message.Write'>"
    assert repr(Message.ChangeColor) == "<class 'fieldenum._fieldenum.Message.ChangeColor'>"
    assert repr(Message.Pause) == "<class 'fieldenum._fieldenum.Message.Pause'>"
    assert repr(Message.FunctionVariant) == "<class 'fieldenum._fieldenum.Message.FunctionVariant'>"


def test_multiple_assignment():
    variant = Variant(x=int)
    @fieldenum
    class OneVariant:
        my = variant
    assert variant.attached
    with pytest.raises(TypeError, match="This variants already attached to"):
        @fieldenum
        class AnotherVariant:
            my = variant
    with pytest.raises(TypeError, match="This variants already attached to"):
        variant.attach(object, eq=True, build_hash=True, build_repr=True, frozen=True)


def test_function_variant():
    message = Message.FunctionVariantWithBody(1, 2, "hello", d=123, f=1.3, e={"hello": "world"})
    assert message.dump() == dict(a=1, b=2, c="hello", d=123, f=1.3, e={"hello": "world"}, raise_it=False)
    try:
        Message.FunctionVariantWithBody(1, 2, "hello", d=123, f=1.3, e={"hello": "world"}, raise_it=True)
    except ExceptionForTest as exc:
        message, *others = exc.value
        assert isinstance(message, Message)
        assert isinstance(message, Message.FunctionVariantWithBody)
        assert others == [1, 2, "hello", 123, 1.3, {"hello": "world"}]

    message = Message.FunctionVariant(1, 2, "hello", d=123, f=1.3, e={"hello": "world"})
    assert message.dump() == dict(a=1, b=2, c="hello", d=123, f=1.3, e={"hello": "world"})

    message = Message.FunctionVariant(1, 2, "hello", d=123)
    assert message.dump() == dict(a=1, b=2, c="hello", d=123, f=0.0, e={"hello": "good"})

    with pytest.raises(TypeError, match="Initializer should return None."):
        Message.NotNoneReturnFunctionVariant(1, 2, "hello", d=123, f=1.3, e={"hello": "world"})


def test_method_abuse_on_function_variant():
    @variant
    def MyVariant(self, hello, world):
        raise ValueError

    with pytest.raises(TypeError, match="method cannot be used in function variant"):
        @fieldenum
        class NeverGonnaBeUsed:
            V = MyVariant.kw_only()

    with pytest.raises(TypeError, match="method cannot be used in function variant"):
        @fieldenum
        class NeverGonnaBeUsed:
            V = MyVariant.default(hello=123)
