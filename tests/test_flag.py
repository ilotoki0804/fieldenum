from email.errors import MessageError
import pytest
from fieldenum import Flag
from fieldenum.enums import Message

def test_flag():
    flag = Flag()
    flag.add(Message.Move(1, 2))
    flag.add(Message.Quit)
    flag.add(Message.ChangeColor(1, 2, 3))

    assert Message.Move(1, 2) in flag
    assert Message.Move(3, 5) not in flag
    assert Message.Quit in flag
    assert set(flag) == {
        Message.Move(1, 2),
        Message.Quit,
        Message.ChangeColor(1, 2, 3),
    }

    flag.add(Message.Move(4, 5))
    assert Message.Move(4, 5) in flag

    assert len(flag) == 3
    assert repr(flag) == "Flag([Message.Move(x=4, y=5), Message.Quit, Message.ChangeColor(1, 2, 3)])"

    assert Message.Pause() not in flag
    flag.add(Message.Pause())
    assert Message.Pause() in flag

    assert len(flag) == 4
    flag.discard(Message.Move(3, 4))
    assert len(flag) == 4
    assert Message.Move(4, 5) in flag
    flag.discard(Message.Move(4, 5))
    assert len(flag) == 3

    flag.add(Message.Move(1, 2))
    assert len(flag) == 4
    with pytest.raises(KeyError):
        flag.remove(Message.Move(4, 2))
    flag.remove(Message.Move(1, 2))
    assert len(flag) == 3

    with pytest.raises(ValueError):
        Flag({})

    flag.clear()
    assert not flag


def test_mixins():
    flag = Flag()
    flag.add(Message.Move(1, 2))
    flag.add(Message.Quit)
    flag.add(Message.ChangeColor(1, 2, 3))

    flag2 = Flag()
    flag2.add(Message.Move(1, 2))
    flag2.add(Message.Quit)
    flag2.add(Message.ChangeColor(1, 2, 3))

    assert flag == flag2
    assert flag.isdisjoint(Flag([Message.Write("hello")]))
    assert not flag.isdisjoint(flag2)
    assert flag > Flag([Message.Quit])

    flag -= {Message.Move(1, 2)}
    assert flag == Flag([Message.Quit, Message.ChangeColor(1, 2, 3)])

    new_flag = flag | Flag([
        Message.Move(4, 5),
        Message.Write("hello")
    ])
    assert new_flag == Flag([
        Message.Move(4, 5),
        Message.Write("hello"),
        Message.Quit,
        Message.ChangeColor(1, 2, 3),
    ])


def test_adapter():
    flag = Flag()
    flag.add(Message.Move(1, 2))
    flag.add(Message.Quit)
    flag.add(Message.ChangeColor(1, 2, 3))

    adapter = flag.variants
    assert Message.Move in adapter
    assert Message.Quit in adapter  # type: ignore
    assert Message.ChangeColor in adapter

    assert len(adapter) == 3
    assert set(adapter) == {
        Message.Move,
        Message.Quit,
        Message.ChangeColor,
    }
    
    with pytest.raises(TypeError):
        adapter & 2  # type: ignore
    with pytest.raises(TypeError):
        () & adapter  # type: ignore
    with pytest.raises(TypeError):
        adapter - 2  # type: ignore
    with pytest.raises(TypeError):
        () - adapter  # type: ignore
    with pytest.raises(TypeError):
        adapter | ()  # type: ignore
    with pytest.raises(TypeError):
        () | adapter  # type: ignore
    with pytest.raises(TypeError):
        adapter |= ()  # type: ignore
    with pytest.raises(TypeError):
        adapter ^ ()  # type: ignore
    with pytest.raises(TypeError):
        () ^ adapter  # type: ignore
    with pytest.raises(TypeError):
        adapter ^= ()  # type: ignore
    with pytest.raises(TypeError):
        adapter == ()  # type: ignore
    with pytest.raises(TypeError):
        adapter &= 2  # type: ignore

    assert adapter & {Message.Move, Message.Quit, Message.Pause} == Flag([
        Message.Move(1, 2),
        Message.Quit,
    ])
    adapter &= {Message.Move, Message.Quit, Message.Pause}
    assert flag == Flag([
        Message.Move(1, 2),
        Message.Quit,
    ])
    assert len(adapter) == 2
    flag.variants &= {Message.Move, Message.Pause}
    assert len(adapter) == 1
    flag.add(Message.Quit)

    assert set(adapter - {Message.Move}) == {Message.Quit}
    flag.add(Message.Move(3, 4))
    flag.add(Message.Pause())
    flag.add(Message.ChangeColor(1, 2, 3))
    assert set(adapter - {Message.Quit}) == {
        Message.Move(3, 4),
        Message.Pause(),
        Message.ChangeColor(1, 2, 3),
    }
    flag.add(Message.Quit)
    adapter -= {Message.Pause, Message.ChangeColor}
    assert set(flag) == {
        Message.Move(3, 4),
        Message.Quit
    }
    flag.discard(Message.Pause)
    assert set(flag) == {
        Message.Move(3, 4),
        Message.Quit
    }
    # This will introduce type checker error but I can't do much :(
    adapter.discard(Message.Quit)  # type: ignore
    assert set(flag) == {
        Message.Move(3, 4),
    }
    adapter.discard(Message.Move)
    assert not flag
    with pytest.raises(TypeError):
        adapter.isdisjoint((Message.Quit,))  # type: ignore
    with pytest.raises(TypeError):
        adapter.add(Message.Quit)  # type: ignore
    with pytest.raises(TypeError):
        adapter.add(Message.Move(1, 2))  # type: ignore

    with pytest.raises(KeyError):
        adapter.remove(Message.Quit)  # type: ignore
    with pytest.raises(KeyError):
        adapter.remove(Message.Move)
    flag |= (Message.Quit, Message.Move(1, 2))  # type: ignore
    assert len(flag) == 2
    adapter.remove(Message.Quit)  # type: ignore
    adapter.remove(Message.Move)
    assert not flag

    flag |= (Message.Quit, Message.Move(1, 2))  # type: ignore
    del adapter[Message.Quit]
    del adapter[Message.Move]
    assert not flag

    flag |= (Message.Quit, Message.Move(1, 2))  # type: ignore
    with pytest.raises(TypeError):
        adapter[Message.Move] = Message.Move(4, 5)  # type: ignore
    assert Message.Move(1, 2) in flag

    assert adapter[Message.Quit] == Message.Quit  # type: ignore
    assert adapter[Message.Move] == Message.Move(1, 2)

    assert {adapter.popitem(), adapter.popitem()} == {
        (Message.Quit, Message.Quit),
        (Message.Move, Message.Move(1, 2))
    }
    with pytest.raises(KeyError):
        adapter.popitem()

    flag |= (Message.Quit, Message.Move(1, 2))  # type: ignore

    assert adapter.get(Message.Quit) == Message.Quit
    assert adapter.get(Message.Move, 123) == Message.Move(1, 2)
    assert adapter.get(Message.Pause, 123) == 123
    assert adapter.get(Message.ChangeColor) is None

    with pytest.raises(KeyError):
        adapter.pop(Message.ChangeColor)  # type: ignore
    assert adapter.pop(Message.ChangeColor, 2) == 2
    assert adapter.pop(Message.Quit) == Message.Quit  # type: ignore
    assert adapter.pop(Message.Move, 5) == Message.Move(1, 2)  # type: ignore

    with pytest.raises(TypeError):
        adapter.update(Message.Quit)  # type: ignore
    with pytest.raises(TypeError):
        adapter.update(Message.ChangeColor(1, 2, 3))  # type: ignore

    flag |= (Message.Quit, Message.Move(1, 2))  # type: ignore
    assert flag
    adapter.clear()
    assert not flag

    flag |= (Message.Quit, Message.Move(1, 2))  # type: ignore
    adapter -= adapter
    assert not flag

    flag |= (Message.Quit, Message.Move(1, 2))  # type: ignore
    assert set(adapter.items()) == {
        (Message.Quit, Message.Quit),
        (Message.Move, Message.Move(1, 2))
    }
