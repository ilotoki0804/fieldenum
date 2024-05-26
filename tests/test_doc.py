# type: ignore


def test_decorator():
    from fieldenum import Unit, Variant, fieldenum

    @fieldenum
    class Message:
        Quit = Unit
        Write = Variant(str)


def test_unitcase():
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
