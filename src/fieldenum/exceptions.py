class FieldEnumError(Exception):
    pass


class NotAllowedError(FieldEnumError):
    pass


class Unreachable(BaseException):
    pass


def unreachable(value=None):
    raise Unreachable(
        "This code meant to be unreachable, but somehow the code reached here. "
        "If you are user, tell developers to fix the issue." + f" Value: {value!r}" * (value is not None)
    )


class TypeCheckFailedError(FieldEnumError):
    pass


class UnwrapFailedError(FieldEnumError):
    pass
