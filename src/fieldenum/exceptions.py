_MISSING = object()


class FieldEnumError(Exception):
    pass


class Unreachable(BaseException):
    pass


def unreachable(value=_MISSING):
    raise Unreachable(
        "This code is meant to be unreachable, but somehow the code reached here. "
        "If you reached here, address developers to fix the issue." + f" Value: {value!r}" * (value is not _MISSING)
    )


class TypeCheckFailedError(FieldEnumError):
    pass
