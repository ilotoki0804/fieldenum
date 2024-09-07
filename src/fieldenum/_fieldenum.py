"""fieldenum core implementation."""

from __future__ import annotations

import copyreg
import inspect
import typing
from contextlib import suppress

from ._utils import NotAllowed, OneTimeSetter, ParamlessSingletonMeta, unpickle
from .exceptions import unreachable

T = typing.TypeVar("T")


class Variant:
    __slots__ = ("name", "field", "attached", "_slots_names", "_base", "_generics", "_actual", "_defaults_and_factories", "_kw_only")

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None) -> typing.Self:
        if self.attached:
            # This is needed in order to make match statements work.
            return self._actual  # type: ignore

        return self

    def kw_only(self) -> typing.Self:
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
        self._defaults_and_factories = {}
        if tuple_field and named_field:
            raise TypeError("Cannot mix tuple fields and named fields. Use named fields.")
        self.field = (tuple_field, named_field)
        if named_field:
            self._slots_names = tuple(named_field)
        else:
            self._slots_names = tuple(f"_{i}" for i in range(len(tuple_field)))

    if typing.TYPE_CHECKING:
        def dump(self): ...

    def default(self, **defaults_and_factories) -> typing.Self:
        _, named_field = self.field
        if not named_field:
            raise TypeError("Only named variants can have defaults.")

        self._defaults_and_factories.update(defaults_and_factories)
        return self

    def attach(
        self,
        cls,
        /,
        *,
        eq: bool,
        build_hash: bool,
        frozen: bool,
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
                        setattr(self, name, value)

                    post_init = getattr(self, "__post_init__", lambda: None)
                    post_init()

            self._actual = TupleConstructedVariant

        elif named_field:
            class NamedConstructedVariant(ConstructedVariant):
                __name__ = item.name
                __qualname__ = f"{cls.__qualname__}.{item.name}"
                __fields__ = item._slots_names
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

                    if item._defaults_and_factories:
                        for name, default_or_factory in item._defaults_and_factories.items():
                            if name not in kwargs:
                                kwargs[name] = factory._produce_from(default_or_factory)

                    if missed_keys := kwargs.keys() ^ named_field.keys():
                        raise TypeError(f"Key mismatch: {missed_keys}")

                    for name in named_field:
                        value = kwargs[name]
                        # field = named_field[name]
                        setattr(self, name, value)

                    post_init = getattr(self, "__post_init__", lambda: None)
                    post_init()

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
                    post_init = getattr(self, "__post_init__", lambda: None)
                    post_init()

            self._actual = FieldlessConstructedVariant
        # fmt: on

        copyreg.pickle(self._actual, self._actual._pickle)
        self.attached = True

    def __call__(self, *args, **kwargs):
        return self._actual(*args, **kwargs)


def variant(cls=None, kw_only: bool = False):
    if cls is None:
        return lambda cls: variant(cls, kw_only)

    fields = cls.__annotations__
    defaults = {field_name: getattr(cls, field_name) for field_name in fields if hasattr(cls, field_name)}

    constructed = Variant(**fields).default(**defaults)
    if kw_only:
        constructed = constructed.kw_only()
    return constructed


class factory(typing.Generic[T]):
    def __init__(self, func: typing.Callable[[], T]):
        self.__factory = func

    @classmethod
    def _produce_from(cls, value: factory[T] | T) -> T:
        return value.produce() if isinstance(value, factory) else value  # type: ignore

    def produce(self) -> T:
        return self.__factory()


# MARK: UnitDescriptor


class UnitDescriptor:
    __slots__ = ("name",)
    __fields__ = ()

    def __init__(self, name: str | None = None):
        self.name = name

    def __set_name__(self, owner, name):
        setattr(owner, name, UnitDescriptor(name))

    @typing.overload
    def __get__(self, obj, objtype: type[T] = ...) -> T: ...  # type: ignore

    @typing.overload
    def __get__(self, obj, objtype: None = ...) -> typing.Self: ...

    def __get__(self, obj, objtype: type[T] | None = None) -> T | typing.Self:
        return self

    def attach(
        self,
        cls,
        /,
        *,
        eq: bool,  # not needed since nothing to check equality
        build_hash: bool,
        frozen: bool,
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
):
    if cls is None:
        return lambda cls: fieldenum(
            cls,
            eq=eq,
            frozen=frozen,
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
    build_hash = eq and not has_own_hash

    for attr in class_attributes.values():
        if isinstance(attr, Variant | UnitDescriptor):
            attr.attach(
                cls,
                eq=eq,
                build_hash=build_hash,
                frozen=frozen,
            )

    with suppress(Exception):
        cls.__init__ = NotAllowed("A base fieldenum cannot be initialized.", name="__init__")

    return typing.final(cls)
