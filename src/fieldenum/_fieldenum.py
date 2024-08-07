"""fieldenum core implementation."""

from __future__ import annotations

import copyreg
import types
import typing
import warnings
from contextlib import suppress

from ._utils import NotAllowed, OneTimeSetter, ParamlessSingletonMeta, unpickle
from .exceptions import unreachable

Base = typing.TypeVar("Base")


class Variant:
    __slots__ = ("name", "field", "attached", "_slots_names", "_base", "_generics", "_actual", "_defaults", "_kw_only")

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None) -> typing.Self:
        if self.attached:
            # This is needed in order to make match statements work.
            return self._actual  # type: ignore

        return self

    @classmethod
    def kw_only(cls, **named_field):
        self = cls(**named_field)
        self._kw_only = True
        return self

    # fieldless variant
    @typing.overload
    def __init__(self) -> None: ...

    # tuple variant
    @typing.overload
    def __init__(self, *tuple_field) -> None: ...

    # named variant
    @typing.overload
    def __init__(self, **named_field) -> None: ...

    def __init__(self, *tuple_field, **named_field) -> None:
        self.attached = False
        self._kw_only = False
        self._defaults = {}
        if tuple_field and named_field:
            raise TypeError("Cannot mix tuple fields and named fields. Use named fields.")
        self.field = (tuple_field, named_field)
        if named_field:
            self._slots_names = tuple(named_field)
        else:
            self._slots_names = tuple(f"_{i}" for i in range(len(tuple_field)))

    if typing.TYPE_CHECKING:
        def dump(self): ...

    def check_type(self, field, value, /):
        """Should raise error when type is mismatched."""

        if field in (typing.Any, typing.Self):
            return

        if type(field) in (
            typing.TypeAlias, types.GenericAlias, typing.TypeVar,  # typing-only things
            getattr(typing, "TypeAliasType", None),  # type aliases (added in python 3.12)
            str,  # possibly type alias
        ):
            return

        try:
            if isinstance(value, field):
                return
        except TypeError:
            warnings.warn(
                f"`isinstance` raised TypeError which mean type of field({field!r}, type: {type(field).__name__}) is not supported. "
                "Contact developer to `check_type` supports it."
            )
            return

        raise TypeError(f"Type of value is not expected. Expected type: {field!r}, actual type: {type(value)!r} and value: {value!r}")

    def with_default(self, **defaults) -> typing.Self:
        """**Experimental Feature**"""
        _, named_field = self.field
        if not named_field:
            raise TypeError("Only named variants can have defaults.")

        self._defaults = defaults
        return self

    def attach(
        self,
        cls,
        /,
        *,
        eq: bool,
        build_hash: bool,
        frozen: bool,
        runtime_check: bool,
    ) -> None | typing.Self:
        if self.attached:
            raise TypeError(f"This variants already attached to {self._base.__name__!r}.")

        self._base = cls
        tuple_field, named_field = self.field
        if not self._kw_only:
            named_field_keys = tuple(named_field)
        item = self

        self._actual: ConstructedVariant

        # fmt: off
        class ConstructedVariant(cls):
            if frozen and not typing.TYPE_CHECKING:
                __slots__ = tuple(f"__original_{name}" for name in item._slots_names)
                for name in item._slots_names:
                    # to prevent potential security risk
                    if name.isidentifier():
                        exec(f"{name} = OneTimeSetter()")
                    else:
                        unreachable(name)
                        OneTimeSetter()  # Show IDEs that OneTimeSetter is used. Not executed at runtime.
            else:
                __slots__ = item._slots_names

        if tuple_field:
            class TupleConstructedVariant(ConstructedVariant):
                __name__ = item.name
                __qualname__ = f"{cls.__qualname__}.{item.name}"
                __fields__ = tuple(range(len(tuple_field)))
                __slots__ = ()
                __match_args__ = item._slots_names

                if build_hash:
                    __slots__ += ("_hash",)

                    if frozen:
                        def __hash__(self) -> int:
                            with suppress(AttributeError):
                                return self._hash

                            self._hash = hash(self.dump())
                            return self._hash
                    else:
                        __hash__ = None  # type: ignore

                if eq:
                    def __eq__(self, other: typing.Self):
                        return type(self) is type(other) and self.dump() == other.dump()

                def __repr__(self) -> str:
                    values_repr = ", ".join(repr(getattr(self, f"_{name}" if isinstance(name, int) else name)) for name in self.__fields__)
                    return f"{item._base.__name__}.{self.__name__}({values_repr})"

                @staticmethod
                def _pickle(variant):
                    assert isinstance(variant, ConstructedVariant)
                    return unpickle, (cls, self.name, tuple(getattr(variant, f"_{i}") for i in variant.__fields__))

                def dump(self) -> tuple:
                    return tuple(getattr(self, f"_{name}") for name in self.__fields__)

                def __init__(self, *args) -> None:
                    if len(tuple_field) != len(args):
                        raise TypeError(f"Expect {len(tuple_field)} field(s), but received {len(args)} argument(s).")

                    for name, field, value in zip(item._slots_names, tuple_field, args, strict=True):
                        if runtime_check:
                            getattr(self, "check_type", item.check_type)(field, value)
                        setattr(self, name, value)
            self._actual = TupleConstructedVariant

        elif named_field:
            class NamedConstructedVariant(ConstructedVariant):
                __name__ = item.name
                __qualname__ = f"{cls.__qualname__}.{item.name}"
                __fields__ = item._slots_names
                __defaults__ = item._defaults
                __slots__ = ()
                if not item._kw_only:
                    __match_args__ = item._slots_names

                if build_hash:
                    __slots__ += ("_hash",)

                    if frozen:
                        def __hash__(self) -> int:
                            with suppress(AttributeError):
                                return self._hash

                            self._hash = hash(tuple(self.dump().items()))
                            return self._hash
                    else:
                        __hash__ = None  # type: ignore

                if eq:
                    def __eq__(self, other: typing.Self):
                        return type(self) is type(other) and self.dump() == other.dump()

                @staticmethod
                def _pickle(variant):
                    assert isinstance(variant, ConstructedVariant)
                    return unpickle, (cls, self.name, {name: getattr(variant, name) for name in variant.__fields__})

                def dump(self):
                    return {name: getattr(self, name) for name in self.__fields__}

                if eq:
                    def __eq__(self, other: typing.Self):
                        return type(self) is type(other) and self.dump() == other.dump()

                def __repr__(self) -> str:
                    values_repr = ', '.join(f'{name}={getattr(self, f"_{name}" if isinstance(name, int) else name)!r}' for name in self.__fields__)
                    return f"{item._base.__name__}.{self.__name__}({values_repr})"

                def __init__(self, *args, **kwargs) -> None:
                    if args:
                        if item._kw_only:
                            raise TypeError(f"Variant '{type(self).__qualname__}' is keyword only.")

                        if len(args) > len(named_field_keys):
                            raise TypeError(f"{self.__name__} takes {len(named_field_keys)} positional argument(s) but {len(args)} were/was given")

                        # a valid use case of zip without strict=True
                        for arg, field_name in zip(args, named_field_keys):
                            if field_name in kwargs:
                                raise TypeError(f"Inconsistent input for field '{field_name}': received both positional and keyword values")
                            kwargs[field_name] = arg

                    if self.__defaults__:
                        kwargs = self.__defaults__ | kwargs

                    if missed_keys := kwargs.keys() ^ named_field.keys():
                        raise TypeError(f"Key mismatch: {missed_keys}")

                    for name in named_field:
                        value = kwargs[name]
                        field = named_field[name]

                        if runtime_check:
                            getattr(self, "check_type", item.check_type)(field, value)
                        setattr(self, name, value)

            self._actual = NamedConstructedVariant

        else:
            class FieldlessConstructedVariant(ConstructedVariant, metaclass=ParamlessSingletonMeta):
                __name__ = item.name
                __qualname__ = f"{cls.__qualname__}.{item.name}"
                __fields__ = ()
                __slots__ = ()

                if build_hash and not frozen:
                    __hash__ = None  # type: ignore
                else:
                    def __hash__(self):
                        return hash(id(self))

                @staticmethod
                def _pickle(variant):
                    assert isinstance(variant, ConstructedVariant)
                    return unpickle, (cls, self.name, ())

                def dump(self):
                    return ()

                def __repr__(self) -> str:
                    values_repr = ""
                    return f"{item._base.__name__}.{self.__name__}({values_repr})"

                def __init__(self) -> None:
                    pass
            self._actual = FieldlessConstructedVariant
        # fmt: on

        copyreg.pickle(self._actual, self._actual._pickle)
        self.attached = True

    def __call__(self, *args, **kwargs):
        return self._actual(*args, **kwargs)


# MARK: UnitDescriptor


class UnitDescriptor:
    __slots__ = ("name",)
    __fields__ = ()

    def __init__(self, name: str | None = None):
        self.name = name

    def __set_name__(self, owner, name):
        setattr(owner, name, UnitDescriptor(name))

    @typing.overload
    def __get__(self, obj, objtype: type[Base] = ...) -> Base: ...  # type: ignore

    @typing.overload
    def __get__(self, obj, objtype: None = ...) -> typing.Self: ...

    def __get__(self, obj, objtype: type[Base] | None = None) -> Base | typing.Self:
        return self

    def attach(
        self,
        cls,
        /,
        *,
        eq: bool,  # not needed since nothing to check equality
        build_hash: bool,
        frozen: bool,
        runtime_check: bool,  # nothing to check
    ):
        if self.name is None:
            raise TypeError("`self.name` is not set.")

        class UnitConstructedVariant(cls, metaclass=ParamlessSingletonMeta):
            __name__ = self.name
            __slots__ = ()
            __fields__ = None  # `None` means it does not require calling for initialize.

            if build_hash and not frozen:
                __hash__ = None  # type: ignore # Explicitly disable hash
            else:
                def __hash__(self):
                    return hash(id(self))

            def dump(self):
                return None

            @staticmethod
            def _pickle(variant):
                assert isinstance(variant, UnitConstructedVariant)
                return unpickle, (cls, self.name, None)

            def __init__(self):
                pass

            def __repr__(self):
                return f"{cls.__name__}.{self.__name__}"

        copyreg.pickle(UnitConstructedVariant, UnitConstructedVariant._pickle)

        # This will replace Unit to Specialized instance.
        setattr(cls, self.name, UnitConstructedVariant())


Unit = UnitDescriptor()


def fieldenum(
    cls=None,
    /,
    *,
    eq: bool = True,
    frozen: bool = True,
    runtime_check: bool = False,
):
    if cls is None:
        return lambda cls: fieldenum(
            cls,
            eq=eq,
            frozen=frozen,
            runtime_check=runtime_check,
        )

    # Preventing subclassing fieldenums at runtime.
    # This also prevent double decoration.
    is_final = False
    for base in cls.mro()[1:]:
        with suppress(Exception):
            if base.__final__:
                is_final = True
                break
    if is_final:
        raise TypeError(
            "One of the base classes of fieldenum class is marked as final, "
            "which means it does not want to be subclassed and it may be fieldenum class, "
            "which should not be subclassed."
        )

    class_attributes = vars(cls)
    has_own_hash = "__hash__" in class_attributes

    for attr in class_attributes.values():
        if isinstance(attr, Variant | UnitDescriptor):
            attr.attach(
                cls,
                eq=eq,
                build_hash=eq and not has_own_hash,
                frozen=frozen,
                runtime_check=runtime_check,
            )

    with suppress(Exception):
        cls.__init__ = NotAllowed("Base fieldenums cannot be initialized.", name="__init__")

    return typing.final(cls)
