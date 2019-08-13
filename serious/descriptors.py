from __future__ import annotations

__all__ = ['TypeDescriptor', 'describe', 'DescTypes', 'scan_types']
__doc__ = """Descriptors of types used by serious. 

Descriptors are simplifying work with types, enriching them with more contextual information.
This allows to make decisions, like picking a serializer, easier.

They unwrap the generic aliases, get generic parameters from parent classes, simplify optional,
dataclass checks and more.

The data is carried by `TypeDescriptor`s which are created by a call to `serious.descriptors.describe(cls)`.
"""
from collections import ChainMap
from dataclasses import dataclass, fields, is_dataclass
from typing import Type, Any, TypeVar, get_type_hints, Dict, Mapping, List, Union, Iterable

from .types import FrozenDict, FrozenList

T = TypeVar('T')

GenericParams = Mapping[Any, 'TypeDescriptor']


@dataclass(frozen=True)
class TypeDescriptor:
    _cls: Type
    parameters: FrozenDict[Any, TypeDescriptor]
    is_optional: bool = False
    is_dataclass: bool = False

    @property
    def cls(self):  # Python fails when providing cls as a keyword parameter to dataclasses
        return self._cls

    @property
    def fields(self) -> Mapping[str, TypeDescriptor]:
        """A mapping of all dataclass field names to their corresponding Type Descriptors.

        Returns an empty mapping if the object is not a dataclass."""
        if not is_dataclass(self.cls):
            return {}
        types = get_type_hints(self.cls)  # type: Dict[str, Type]
        descriptors = {name: self.describe(type_) for name, type_ in types.items()}
        return {f.name: descriptors[f.name] for f in fields(self.cls)}

    def describe(self, type_: Type) -> TypeDescriptor:
        return describe(type_, self.parameters)


def describe(type_: Type, generic_params: GenericParams = None) -> TypeDescriptor:
    """Creates a TypeDescriptor for the provided type.

    Optionally generic params can be designated as a mapping of TypeVar to parameter Type or indexes in Dict/List/etc.
    """
    generic_params = generic_params if generic_params is not None else {}
    param = generic_params.get(type_, None)
    if param is not None:
        return param
    return _describe_generic(type_, generic_params)


_any_type_desc = TypeDescriptor(Any, FrozenDict())  # type: ignore
_generic_params: Dict[Type, Dict[int, TypeDescriptor]] = {
    list: {0: _any_type_desc},
    set: {0: _any_type_desc},
    frozenset: {0: _any_type_desc},
    tuple: {0: _any_type_desc, 1: TypeDescriptor(Ellipsis, FrozenDict())},  # type: ignore
    dict: {0: _any_type_desc, 1: _any_type_desc},
}


def _get_default_generic_params(cls: Type, params: GenericParams) -> GenericParams:
    """Returns mapping of default generic params for the provided cls.

    Examples:
    - `dict` -> {0: <TypeDescriptor cls=Any>, 1: <TypeDescriptor cls=Any>};
    - `list` -> {0: <TypeDescriptor cls=Any>};
    - `tuple` -> {0: <TypeDescriptor cls=Any>, 1: <TypeDescriptor cls=Ellipses>}.
    """
    for generic, default_params in _generic_params.items():
        if issubclass(cls, generic):
            return default_params
    return params


def _describe_generic(cls: Type, generic_params: GenericParams) -> TypeDescriptor:
    """Creates a TypeDescriptor for Python _GenericAlias, unwrapping it to its origin/

    Examples:
    - Tuple[str] -> <TypeDescriptor cls=tuple params={0: <TypeDescriptor cls=str>}>
    - Optional[int] -> <TypeDescriptor cls=int is_optional=True>
    """
    params: GenericParams = {}
    is_optional = _is_optional(cls)
    if is_optional:
        cls = cls.__args__[0]
    if hasattr(cls, '__orig_bases__') and is_dataclass(cls):
        params = dict(ChainMap(*(_describe_generic(base, generic_params).parameters for base in cls.__orig_bases__)))
        return TypeDescriptor(
            cls,
            parameters=FrozenDict(params),
            is_optional=is_optional,
            is_dataclass=True
        )
    if hasattr(cls, '__origin__'):
        origin_is_dc = is_dataclass(cls.__origin__)
        if origin_is_dc:
            params = _collect_type_vars(cls, generic_params)
        else:
            describe_ = lambda arg: describe(Any if type(arg) is TypeVar else arg, generic_params)
            params = dict(enumerate(map(describe_, cls.__args__)))
        return TypeDescriptor(
            cls.__origin__,
            parameters=FrozenDict(params),
            is_optional=is_optional,
            is_dataclass=origin_is_dc
        )
    if isinstance(cls, type) and len(params) == 0:
        params = _get_default_generic_params(cls, params)
    return TypeDescriptor(
        cls,
        parameters=FrozenDict(params),
        is_optional=is_optional,
        is_dataclass=is_dataclass(cls)
    )


def _collect_type_vars(alias: Any, generic_params: GenericParams) -> GenericParams:
    return dict(zip(alias.__origin__.__parameters__,
                    (describe(arg, generic_params) for arg in alias.__args__)))


class DescTypes:
    types: FrozenList[Type]

    def __init__(self, types: Iterable[Type]):
        super().__setattr__('types', FrozenList(types))

    @classmethod
    def scan(cls, desc: TypeDescriptor, *, known: List[TypeDescriptor]) -> 'DescTypes':
        if desc in known:
            return _empty_desc_types
        known.append(desc)
        dts = []  # type: List[DescTypes]
        for param in desc.parameters.values():
            dts.append(cls.scan(param, known=known))
        for child_desc in desc.fields.values():
            dts.append(cls.scan(child_desc, known=known))
        types = [type_ for dt in dts for type_ in dt.types]
        types.append(desc.cls)
        return cls(types)

    def __setattr__(self, key, value):
        raise AttributeError('Attempt to modify an immutable object')

    def __contains__(self, item):
        return item in self.types


_empty_desc_types = DescTypes({})


def scan_types(desc: TypeDescriptor) -> DescTypes:
    """Create a DescTypes object for the provided descriptor.

    DescTypes allow checks of the descriptor tree."""
    return DescTypes.scan(desc, known=[])


def _is_optional(cls: Type) -> bool:
    """Returns True if the provided type is Optional."""
    return getattr(cls, '__origin__', None) == Union \
           and len(cls.__args__) == 2 \
           and cls.__args__[1] == type(None)
