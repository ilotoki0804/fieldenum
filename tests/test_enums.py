from typing import Any, assert_type
import pytest
from fieldenum import *
from fieldenum.enums import *
from fieldenum.exceptions import IncompatibleBoundError, UnwrapFailedError


def test_option_get():
    list_opt = Option.new(list(range(100)))
    dict_opt = Option.new({f"no{i}": i for i in range(100)})
    other_opt = Option.new(234)

    # Basic get
    assert list_opt.get(3) == Option.Some(3)
    assert list_opt.get(300) is Option.Nothing
    assert dict_opt.get("no4") == Option.Some(4)
    assert dict_opt.get("not_key") is Option.Nothing
    assert other_opt.get(123) is Option.Nothing
    assert_type(list_opt.get(3), Option[int])
    assert_type(list_opt.get(300), Option[int])
    assert_type(dict_opt.get("no4"), Option[int])
    assert_type(dict_opt.get("not_key"), Option[int])
    assert_type(other_opt.get(123), Option)

    # get with a default
    assert list_opt.get(3, default=23) == Option.Some(3)
    assert list_opt.get(3, default="hello") == Option.Some(3)
    assert list_opt.get(300, default=3) == Option.Some(3)
    assert list_opt.get(300, default="hello") == Option.Some("hello")
    assert dict_opt.get("no4", default=35) == Option.Some(4)
    assert dict_opt.get("no4", default="hello") == Option.Some(4)
    assert dict_opt.get("not_key") is Option.Nothing
    assert dict_opt.get("not_key", default=123) == Option.Some(123)
    assert dict_opt.get("not_key", default="e3") == Option.Some("e3")
    assert other_opt.get(123, default="hello") == Option.Some("hello")
    assert_type(list_opt.get(3, default=23), Option[int])
    assert_type(list_opt.get(3, default="hello"), Option[int | str])
    assert_type(list_opt.get(300, default=3), Option[int])
    assert_type(list_opt.get(300, default="hello"), Option[int | str])
    assert_type(dict_opt.get("no4", default=35), Option[int])
    assert_type(dict_opt.get("no4", default="hello"), Option[int | str])
    assert_type(dict_opt.get("not_key"), Option[int])
    assert_type(dict_opt.get("not_key", default=123), Option[int])
    assert_type(dict_opt.get("not_key", default="e3"), Option[int | str])
    assert_type(other_opt.get(123, default="hello"), Option[Any | str])

    # get with nothing
    assert Option.Nothing.get("hello") is Option.Nothing
    # with random methods
    assert Option.Nothing.get("hello", suppress=(), default="others") is Option.Nothing

    # get with exc
    assert list_opt.get(3, suppress=()) == Option.Some(3)
    assert list_opt.get(300, suppress=IndexError) is Option.Nothing
    assert list_opt.get(300, suppress=IndexError | KeyError | TypeError) is Option.Nothing
    assert list_opt.get(300, suppress=(IndexError, TypeError)) is Option.Nothing
    assert dict_opt.get("no4", suppress=()) == Option.Some(4)
    assert dict_opt.get("not_key", suppress=KeyError) is Option.Nothing
    assert other_opt.get(123, suppress=TypeError) is Option.Nothing
    with pytest.raises(IndexError):
        assert list_opt.get(300, suppress=()) is Option.Nothing
    with pytest.raises(IndexError):
        assert list_opt.get(300, suppress=KeyError | TypeError) is Option.Nothing
    with pytest.raises(KeyError):
        assert dict_opt.get("not_key", suppress=TypeError | IndexError) is Option.Nothing
    with pytest.raises(TypeError):
        assert other_opt.get(123, suppress=(KeyError, IndexError)) is Option.Nothing
    with pytest.raises(TypeError):
        assert other_opt.get(123, suppress=KeyError | IndexError) is Option.Nothing

    # compound gets
    complex_dict_opt = Option.new({f"no{i}": i for i in range(100)} | {"hello": {"world": {"spam": "ham"}}})
    assert complex_dict_opt.get("hello").get("world") == Option.Some({"spam": "ham"})
    assert complex_dict_opt.get("hello").get("world").get("spam") == Option.Some("ham")
    assert complex_dict_opt.get("hello").get("world").get("spam").get("hello") is Option.Nothing

    # ignored classes
    str_opt = Option.new("hello, world!")
    assert str_opt.get(7) is Option.Nothing
    assert str_opt.get(7, ignored=()) == Option.Some("w")
    assert str_opt.get(7, ignored=(dict, list)) == Option.Some("w")
    assert list_opt.get(7, ignored=(dict, list)) is Option.Nothing
    assert list_opt.get(7, ignored=dict | list) is Option.Nothing

def test_option():
    assert Option[int].Some(123) == Option.Some(123)  # Can be changed in future.

    # test new
    assert Option.new(123) == Option.Some(123)
    assert Option.new(Option.Some(123)) == Option.Some(Option.Some(123))
    assert Option.new(None) is Option.Nothing
    assert Option.new(Option.Nothing) == Option.Some(Option.Nothing)

    # test unwrap
    option = Option.Some(123)
    assert option._0 == 123
    assert option.unwrap() == 123
    assert ~option == 123
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
    assert Some(123).map(lambda _: None) == Option.Some(None)
    assert Some(123).map(lambda _: Option.Nothing) == Option.Some(Option.Nothing)
    assert Some(123).map(lambda _: Option.Some(567)) == Option.Some(Option.Some(567))

    # test map suppressing
    opt = Some("not an integer").map(int, suppress=ValueError)
    assert_type(opt, Option[int])
    assert opt is Option.Nothing

    opt = Some("not an integer").map(int, suppress=ValueError | TypeError)
    assert_type(opt, Option[int])
    assert opt is Option.Nothing

    opt = Some("123").map(int, suppress=ValueError)
    assert_type(opt, Option[int])
    assert opt == Option.Some(123)

    with pytest.raises(ValueError):
        opt = Some("not an integer").map(int)
    with pytest.raises(ValueError):
        opt = Some("not an integer").map(int, suppress=())

    # test wrap
    @Option.wrap
    def func[T](returns: T) -> T:
        return returns

    assert func(1233) == Some(1233)
    assert func(None) is Option.Nothing

    assert Option.Nothing.setdefault("hello") == Option.Some("hello")
    assert Option.Some("world").setdefault("hello") == Option.Some("world")
    assert_type(Option[str].Nothing.setdefault("hello"), Option[str])
    assert_type(Option[int].Nothing.setdefault("hello"), Option[str | int])
    assert_type(Option.new("world").setdefault("hello"), Option[str])
    assert_type(Option.Some(123).setdefault("hello"), Option[str | int])


def test_bound_result():
    _ = BoundResult[int, Exception].map(
        BoundResult.Success(123, Exception), str
    )  # type should be BoundResult[str, Exception]

    # general features
    assert BoundResult.Success(2342, Exception) == BoundResult.Success(2342, Exception)
    assert BoundResult.Success(1234, Exception).unwrap() == 1234
    assert ~BoundResult.Success(1234, Exception) == 1234
    assert BoundResult.Success(1234, Exception).unwrap(34556) == 1234
    with pytest.raises(ValueError, match="error"):
        BoundResult.Failed(ValueError("error"), ValueError).unwrap()
    assert BoundResult.Failed(Exception("err"), Exception).unwrap(34556) == 34556
    assert BoundResult.Success(False, Exception)
    assert not BoundResult.Failed(Exception("Some exception."), Exception)

    error = ValueError(123)
    def raising(error):
        raise error
    with pytest.raises(ValueError):
        BoundResult.Success(2342, ArithmeticError).map(
            lambda _: raising(error)
        )
    error = ValueError(1234)


    with pytest.raises(SystemExit) as exc:
        BoundResult.Success("success", Exception).exit()
    assert exc.value.code == 0

    with pytest.raises(SystemExit) as exc:
        BoundResult.Failed(error, Exception).exit()
    assert exc.value.code == 1

    with pytest.raises(SystemExit) as exc:
        BoundResult.Failed(error, Exception).exit("failed miserably...")
    assert exc.value.code == "failed miserably..."

    with pytest.raises(SystemExit) as exc:
        BoundResult.Failed(error, Exception).exit(None)
    assert exc.value.code == None

    # test __post_init__ of BoundResult
    with pytest.raises(IncompatibleBoundError, match="not an exception"):
        BoundResult.Success(None, int)  # type: ignore
    with pytest.raises(IncompatibleBoundError, match="not an exception"):
        BoundResult.Failed(ValueError("hello"), int)  # type: ignore
    with pytest.raises(IncompatibleBoundError, match="not compatible"):
        BoundResult.Failed(123, ValueError)  # type: ignore
    with pytest.raises(IncompatibleBoundError, match="not compatible"):
        BoundResult.Failed(Exception(345), ValueError)


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
        exception_bound_func = BoundResult.wrap(Exception, func)
        valueerror_bound_func = BoundResult.wrap(ValueError, func)
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
    assert exception_bound_func(Exception()).as_option() is Option.Nothing

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
        BoundResult.wrap(lambda: None, Exception, "unexpected_param")  # type: ignore
    with pytest.raises(TypeError):
        BoundResult.wrap(lambda: None, Exception, "unexpected_param", "unexpected_param2")  # type: ignore

    assert valueerror_bound_func(None, 1234).bound is ValueError
    assert valueerror_bound_func(ValueError(123), 1234).bound is ValueError
    assert valueerror_bound_func(ValueError(123), 1234).rebound(Exception).bound is Exception

    assert Success("hello", ValueError).map(lambda x: exception_bound_func(None, x)).unwrap() == Success("hello", Exception)
    error = ValueError("hello")
    assert BoundResult.Failed(error, ValueError).map(lambda x: exception_bound_func(None, x)) == BoundResult.Failed(
        error, ValueError
    )


def test_result():
    from fieldenum.enums import Result

    # general features
    assert Result.Ok(2342) == Result.Ok(2342)
    assert Result.Ok(1234).unwrap() == 1234
    assert ~Result.Ok(1234) == 1234
    assert Result.Ok(1234).unwrap(34556) == 1234
    with pytest.raises(ValueError, match="error"):
        Result.Err(ValueError("error")).unwrap()
    assert Result.Err(Exception("err")).unwrap(34556) == 34556
    assert Result.Ok(False)
    assert not Result.Err(Exception("Some exception."))

    error = ValueError(123)
    def raising(error):
        raise error
    with pytest.raises(ValueError):
        Result.Ok(2342).map(
            lambda _: raising(error), ArithmeticError
        )
    error = ValueError(1234)


    with pytest.raises(SystemExit) as exc:
        Result.Ok("success").exit()
    assert exc.value.code == 0

    with pytest.raises(SystemExit) as exc:
        Result.Err(error).exit()
    assert exc.value.code == 1

    with pytest.raises(SystemExit) as exc:
        Result.Err(error).exit("failed miserably...")
    assert exc.value.code == "failed miserably..."

    with pytest.raises(SystemExit) as exc:
        Result.Err(error).exit(None)
    assert exc.value.code == None


@pytest.mark.parametrize(
    "second_param",
    [True, False],
)
def test_result_wrap(second_param):
    from fieldenum.enums import Result

    def func[T](raises: BaseException | None = None, returns: T = None) -> T:
        if raises:
            raise raises
        return returns

    if second_param:
        exception_bound_func = Result.wrap(Exception, func)
        valueerror_bound_func = Result.wrap(ValueError, func)
    else:
        exception_bound_func = Result.wrap(Exception)(func)
        valueerror_bound_func = Result.wrap(ValueError)(func)

    assert exception_bound_func(None, "hello") == Result.Ok("hello")
    match exception_bound_func(ValueError(), "hello"):
        case Result.Err(err):
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
    assert exception_bound_func(Exception()).as_option() is Option.Nothing

    assert exception_bound_func(None, "hello").map(lambda s: s + ", world!", ValueError) == Result.Ok("hello, world!")
    match exception_bound_func(None, "hello").map(lambda s: 1 / 0, Exception):
        case Result.Err(err):
            assert isinstance(err, ZeroDivisionError)
        case other:
            assert False, other
    with pytest.raises(ZeroDivisionError):
        exception_bound_func(None, "hello").map(lambda s: 1 / 0, ValueError)

    with pytest.raises(TypeError):
        Result.wrap(lambda: None, Exception, "unexpected_param")  # type: ignore
    with pytest.raises(TypeError):
        Result.wrap(lambda: None, Exception, "unexpected_param", "unexpected_param2")  # type: ignore

    assert Result.Ok("hello").map(lambda x: exception_bound_func(None, x), ValueError).unwrap() == Result.Ok("hello")
    error = ValueError("hello")
    assert Result.Err(error).map(lambda x: exception_bound_func(None, x), ValueError) == Result.Err(error)

if __name__ == "__main__":
    test_bound_result_wrap(False)
    test_bound_result_wrap(True)
