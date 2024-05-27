# type: ignore

import pytest
from fieldenum import *
from fieldenum.enums import *
from fieldenum.exceptions import UnwrapFailedError


def test_option():
    assert Option[int].Some(123) == Option.Some(123)  # Can be changed in future.

    # test new
    assert Option.new(123) == Option.Some(123)
    assert Option.new(None) == Option.Nothing

    # test unwrap
    option = Option.Some(123)
    assert option._0 == 123
    assert option.unwrap() == 123
    assert option.unwrap(456) == 123
    option = Option.Nothing
    assert option is Option.Nothing
    with pytest.raises(UnwrapFailedError):
        option.unwrap()
    assert option.unwrap("default") == "default"

    # test expect
    option = Option.Some("hello")
    assert option.expect("message") == "hello"
    assert option.expect(ValueError("message")) == "hello"
    option = Option.Nothing
    with pytest.raises(UnwrapFailedError, match="message"):
        option.expect("message")
    with pytest.raises(ValueError, match="message"):
        option.expect(ValueError("message"))

    # test __bool__
    assert Option.Some(False)
    assert not Option.Nothing

    # test map
    option = Option.Some("123")
    assert option.map(int) == Option.Some(123)
    option = Option.Nothing
    assert option.map(int) is Option.Nothing
    assert Some(123).map(lambda _: None) is Option.Nothing

    # test map(func, as_is=True)
    myoption = Some("123")
    assert myoption.map(int, as_is=False).unwrap() == 123
    assert myoption.map(int, as_is=True).unwrap() == 123

    # test map(func, as_is=False, unwrap_result=True)
    @BoundResult.wrap(Exception)
    def add_one(value):
        return value + 1

    assert myoption.map(add_one, unwrap_result=True) == Option.Nothing
    assert Some(123).map(add_one, unwrap_result=True).unwrap() == 124
    with pytest.raises(TypeError):
        Some("123").map(int, unwrap_result=True)
    assert Some(123).map(BoundResult.wrap(lambda _: None, Exception), unwrap_result=True) is Option.Nothing
    assert Some(123).map(BoundResult.wrap(lambda _: Option.Nothing, Exception), unwrap_result=True, as_is=False) is Option.Nothing
    assert Some(123).map(BoundResult.wrap(lambda _: Option.Some(234), Exception), unwrap_result=True, as_is=False) == Option.Some(234)

    # test wrap
    @Option.wrap
    def func(returns):
        return returns

    assert func(1233) == Some(1233)
    assert func(None) == Option.Nothing

def test_bound_result():
    _ = BoundResult[int, Exception].map(
        BoundResult.Success(123, Exception), str
    )  # type should be BoundResult[str, Exception]

    # general features
    assert BoundResult.Success(2342, Exception) == BoundResult.Success(2342, Exception)
    assert BoundResult.Success(1234, Exception).unwrap() == 1234
    assert BoundResult.Success(1234, Exception).unwrap(34556) == 1234
    with pytest.raises(ValueError, match="error"):
        BoundResult.Failed(ValueError("error"), ValueError).unwrap()
    assert BoundResult.Failed(Exception("err"), Exception).unwrap(34556) == 34556
    assert BoundResult.Success(False, Exception)
    assert not BoundResult.Failed(True, Exception)

    assert BoundResult.Success(2342, Exception).map(str, as_is=True) == BoundResult.Success("2342", Exception)
    error = ValueError(123)
    assert BoundResult.Success(2342, Exception).map(lambda _: BoundResult.Failed(error, Exception), as_is=True).unwrap() == BoundResult.Failed(error, Exception)
    error = ValueError(1234)
    assert BoundResult.Failed(error, Exception).map(str, as_is=True) == BoundResult.Failed(error, Exception)


@pytest.mark.parametrize(
    "second_param",
    [True, False],
)
def test_bound_result_wrap(second_param):
    def func[T](raises: BaseException | None = None, returns: T = None) -> T:
        if raises:
            raise raises
        return returns

    if second_param:
        exception_bound_func = BoundResult.wrap(func, Exception)
        valueerror_bound_func = BoundResult.wrap(func, ValueError)
    else:
        exception_bound_func = BoundResult.wrap(Exception)(func)
        valueerror_bound_func = BoundResult.wrap(ValueError)(func)

    assert exception_bound_func(None, "hello") == BoundResult.Success("hello", Exception)
    match exception_bound_func(ValueError(), "hello"):
        case BoundResult.Failed(err, _):
            assert isinstance(err, ValueError)
        case other:
            assert False, other
    with pytest.raises(Exception, match="message"):
        valueerror_bound_func(Exception("message"))
    with pytest.raises(BaseException, match="message"):
        exception_bound_func(BaseException("message"))
    assert exception_bound_func(None, "hello")
    assert not exception_bound_func(ValueError(), "hello")

    assert exception_bound_func(None, "hello").as_option() == Option.Some("hello")
    assert exception_bound_func(Exception()).as_option() == Option.Nothing

    assert exception_bound_func(None, "hello").rebound(ValueError).map(lambda s: s + ", world!") == BoundResult.Success(
        "hello, world!", ValueError
    )
    match exception_bound_func(None, "hello").map(lambda s: 1 / 0):
        case BoundResult.Failed(err, _):
            assert isinstance(err, ZeroDivisionError)
        case other:
            assert False, other
    with pytest.raises(ZeroDivisionError):
        exception_bound_func(None, "hello").rebound(ValueError).map(lambda s: 1 / 0)

    with pytest.raises(TypeError):
        BoundResult.wrap(lambda: None, Exception, "unexpected_param")
    with pytest.raises(TypeError):
        BoundResult.wrap(lambda: None, Exception, "unexpected_param", "unexpected_param2")

    assert valueerror_bound_func(None, 1234).bound is ValueError
    assert valueerror_bound_func(ValueError(123), 1234).bound is ValueError
    assert valueerror_bound_func(ValueError(123), 1234).rebound(Exception).bound is Exception

    assert Success("hello", ValueError).map(lambda x: exception_bound_func(None, x)) == Success("hello", ValueError)
    error = ValueError("hello")
    assert BoundResult.Failed(error, ValueError).map(lambda x: exception_bound_func(None, x), as_is=False) == BoundResult.Failed(error, ValueError)
