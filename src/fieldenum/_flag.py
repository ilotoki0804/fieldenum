from __future__ import annotations

from contextlib import suppress
import typing
from collections.abc import Iterable, MutableMapping, MutableSet

T = typing.TypeVar("T")
U = typing.TypeVar("U")
V = typing.TypeVar("V")
_MISSING = object()


def _get_type_if_unit(variant: T) -> T:
    """Get type if unit, return as is otherwise.

    This function is used for code treating unit variant as a type.
    """
    # You could pass either a class or an instance of the variant.
    if isinstance(variant, type):
        return variant
    try:
        # If variant.__fields__ is None, the variant is treated as Unit variant.
        is_unit = variant.__fields__ is None  # type: ignore
    except AttributeError:
        # Not a variant. Your code should not include those on Flag.
        # It's not tested as well.
        return variant
    else:
        return type(variant) if is_unit else variant


class Flag(typing.Generic[T], MutableSet[T]):
    def __init__(self, flags: typing.Iterable[T] | None = None) -> None:
        if isinstance(flags, dict):
            raise ValueError(
                "Dictionary cannot be flags to avoid common confusion. "
                "Use `flags_keys_dict.keys()` if you *really* want to use dictionary."
            )
        flags_dict: dict[type[T], T] = {type(flag): flag for flag in flags or ()}
        self._flags = flags_dict
        self._adapter = _VariantAdepter(flags_dict, __class__)

    def __contains__(self, other: T) -> bool:
        return type(other) in self._flags and other == self._flags[type(other)]

    def __len__(self) -> int:
        return len(self._flags)

    def __iter__(self) -> typing.Iterator[T]:
        return iter(self._flags.values())

    def __repr__(self) -> str:
        return f"{type(self).__name__}({list(self._flags.values())!r})"

    def add(self, flag: T) -> None:
        self._flags[type(flag)] = flag

    def discard(self, flag: T) -> None:
        try:
            value = self._flags.pop(type(flag))
        except KeyError:
            return
        else:
            if flag != value:
                self.add(value)

    def remove(self, flag: T) -> None:
        value = self._flags.pop(type(flag))
        if value != flag:
            self.add(value)
            raise KeyError(value)

    def clear(self) -> None:
        self._flags.clear()

    @property
    def variants(self) -> _VariantAdepter[T]:
        """Access flags via type."""
        return self._adapter

    @variants.setter
    def variants(self, value) -> None:
        """Fake setter for variants.

        This is used for inplace operations like: `flag.variants &= my_flag`

        This does indeed not set value.
        Use `self._adapter = value` if you *really* want to set value.
        """
        pass


class _VariantAdepter(typing.Generic[T], MutableSet[type[T]], MutableMapping[type[T], T]):
    def __init__(self, flag: dict[type[T], T], variant_constructor: type[Flag]):
        self._flags = flag
        self._constructor = variant_constructor

    # Set dunders

    def __contains__(self, other: type[T]) -> bool:
        return _get_type_if_unit(other) in self._flags

    def __len__(self) -> int:
        return len(self._flags)

    def __and__(self, other) -> Flag[T]:
        if not isinstance(other, Iterable):
            return NotImplemented
        items = []
        for type in other:
            with suppress(KeyError):
                items.append(self[type])
        return self._constructor(items)

    def __iand__(self, other) -> typing.Self:
        if not isinstance(other, Iterable):
            return NotImplemented
        other = {_get_type_if_unit(item) for item in other}
        for type in list(self._flags):  # No concurrent safety
            if type not in other:
                del self._flags[type]
        return self

    def __sub__(self, other) -> Flag[T]:
        if not isinstance(other, Iterable):
            return NotImplemented
        other = {_get_type_if_unit(item) for item in other}
        return self._constructor(
            flag for type, flag in self._flags.items()
            if type not in other
        )

    def __isub__(self, it) -> typing.Self:
        if it is self:
            self.clear()
        else:
            for value in it:
                self.discard(value)
        return self

    def __rand__(self, other: typing.Never):
        return NotImplemented

    def __rsub__(self, other: typing.Never):
        return NotImplemented

    def __or__(self, other: typing.Never):
        return NotImplemented

    def __ror__(self, other: typing.Never):
        return NotImplemented

    def __xor__(self, other: typing.Never):
        return NotImplemented

    def __rxor__(self, other: typing.Never):
        return NotImplemented

    def __ior__(self, it: typing.Never):
        return NotImplemented

    def __ixor__(self, it: typing.Never):
        return NotImplemented

    def isdisjoint(self, other: typing.Never) -> typing.NoReturn:
        """This won't work. Use `flag.isdisjoint()` instead."""
        raise TypeError("Cannot use this method with variant adapter. Use `flag.isdisjoint()` instead.")

    def add(self, object: typing.Never) -> typing.NoReturn:
        """This won't work. Use `flag.add()` instead."""
        raise TypeError("Cannot add to variant adapter. Use `flag.add()` instead.")

    def clear(self) -> None:
        self._flags.clear()

    def discard(self, flag_type: type[T]) -> None:
        self._flags.pop(_get_type_if_unit(flag_type), None)

    def remove(self, flag_type: type[T]) -> None:
        self._flags.pop(_get_type_if_unit(flag_type))

    # Dictionary APIs

    def __iter__(self) -> typing.Iterator[type[T]]:
        for type, value in self._flags.items():
            if type == _get_type_if_unit(value):
                yield value  # type: ignore
            else:
                yield type

    def items(self) -> typing.Iterator[tuple[type[T], T]]:
        for type, value in self._flags.items():
            if type == _get_type_if_unit(value):
                yield value, value  # type: ignore
            else:
                yield type, value

    def __delitem__(self, key) -> None:
        """delete item from flag.

        This method exist only for parity with mappings.
        Use `adapter.remove()` instead.
        """
        del self._flags[_get_type_if_unit(key)]

    def __getitem__(self, key: type[T]) -> T:
        return self._flags[_get_type_if_unit(key)]

    def __setitem__(self, key: typing.Never, value: typing.Never) -> typing.NoReturn:
        """This won't work. Use `flag.add()` instead."""
        raise TypeError("Cannot set item with variant adapter. Use `flag.add()` instead.")

    def __eq__(self, other: typing.Never) -> typing.NoReturn:
        """This won't work. Use `flag == other` instead."""
        raise TypeError("Cannot check equality with variant adapter. Use `flag == other` instead.")

    def popitem(self) -> tuple[type[T], T]:
        type, value = self._flags.popitem()
        if type == _get_type_if_unit(value):
            return value, value  # type: ignore
        else:
            return type, value

    @typing.overload
    def pop(self, flag_type: type[T]) -> T: ...

    @typing.overload
    def pop(self, flag_type: type[T], default: T) -> T: ...

    @typing.overload
    def pop(self, flag_type: type[T], default: U) -> T | U: ...

    def pop(self, flag_type, default=_MISSING):
        flag_type = _get_type_if_unit(flag_type)
        return self._flags.pop(flag_type) if default is _MISSING else self._flags.pop(flag_type, default)

    @typing.overload
    def get(self, flag_type: type[T]) -> T | None: ...

    @typing.overload
    def get(self, flag_type: type[T], default: T) -> T: ...

    @typing.overload
    def get(self, flag_type: type[T], default: U) -> T | U: ...

    def get(self, flag_type, default=_MISSING):
        flag_type = _get_type_if_unit(flag_type)
        return self._flags.get(flag_type) if default is _MISSING else self._flags.get(flag_type, default)

    def update(self, other: typing.Never, /, **kwds: typing.Never) -> typing.NoReturn:
        """This won't work. Use `flag |= to_update` instead."""
        raise TypeError("Cannot update item with variant adapter. Use `flag |= to_update` instead.")
