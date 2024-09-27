"""Internal utilities of fieldenum.

This functions and classes are not meant to be used by users,
which means they can be modified, deleted, or added without notice.
"""

from __future__ import annotations


def unpickle(cls, name: str, args, kwargs):
    Variant = getattr(cls, name)
    if args is None and kwargs is None:
        return Variant
    else:
        return Variant(*args, **kwargs)


class OneTimeSetter:
    def __set_name__(self, owner, name):
        self.name = name
        self.private_name = f"__original_{name}"

    def __get__(self, obj, objtype=None):
        return getattr(obj, self.private_name)

    def __set__(self, obj, value):
        if hasattr(obj, self.private_name):
            raise TypeError(f"Cannot mutate attribute `{self.name}` since it's frozen.")
        setattr(obj, self.private_name, value)


class ParamlessSingletonMeta(type):
    """Singleton implementation for class that does not have any parameter."""
    _instance = None

    def __call__(cls):
        if cls._instance is None:
            cls._instance = super().__call__()
        return cls._instance
