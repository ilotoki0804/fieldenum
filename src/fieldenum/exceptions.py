_MISSING = object()


class FieldEnumError(Exception):
    pass


class NotAllowedError(FieldEnumError):
    pass


class Unreachable(BaseException):
    pass


def unreachable(value=_MISSING):
    raise Unreachable(
        "This code is meant to be unreachable, but somehow the code reached here. "
        "If you are user, tell developers to fix the issue." + f" Value: {value!r}" * (value is not _MISSING)
    )


class TypeCheckFailedError(FieldEnumError):
    pass


class UnwrapFailedError(FieldEnumError):
    pass
