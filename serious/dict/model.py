"""A module with `DictModel` -- Serious model to transform between dataclasses and dictionaries."""
from __future__ import annotations

__all__ = ['DictModel']

from typing import TypeVar, Type, Generic, List, Collection, Dict, Iterable, Any, Mapping, Union

from serious.checks import check_is_instance
from serious.descriptors import describe, TypeDescriptor
from serious.serialization import FieldSerializer, SeriousModel, field_serializers
from serious.utils import class_path

T = TypeVar('T')


class DictModel(Generic[T]):
    """A model convert dataclasses to dicts and back.

    Check __init__ parameters for all of configuration options.
    """
    descriptor: TypeDescriptor
    serializer: SeriousModel

    def __init__(
            self,
            cls: Type[T],
            serializers: Iterable[Type[FieldSerializer]] = field_serializers(),
            *,
            allow_any: bool = False,
            allow_missing: bool = False,
            allow_unexpected: bool = False,
            validate_on_load: bool = True,
            validate_on_dump: bool = False,
            ensure_frozen: Union[bool, Iterable[Type]] = False,
    ):
        """
        :param cls: the dataclass type to load/dump.
        :param serializers: field serializer classes in an order they will be tested for fitness for each field.
        :param allow_any: `False` to raise if the model contains fields annotated with `Any`
                (this includes generics like `List[Any]`, or simply `list`).
        :param allow_missing: `False` to raise during load if data is missing the optional fields.
        :param allow_unexpected: `False` to raise during load if data contains some unknown fields.
        :param validate_on_load: to call dataclass `__validate__` method after object construction.
        :param validate_on_dump: to call object `__validate__` before dumping.
        :param ensure_frozen: `False` to skip check of model immutability; `True` will perform the check
                against built-in immutable types; a list of custom immutable types is added to built-ins.
        """
        self.cls = cls
        self.descriptor = describe(cls)
        self.serializer = SeriousModel(
            self.descriptor,
            serializers,
            allow_any=allow_any,
            allow_missing=allow_missing,
            allow_unexpected=allow_unexpected,
            validate_on_load=validate_on_load,
            validate_on_dump=validate_on_dump,
            ensure_frozen=ensure_frozen,
        )

    def load(self, data: Dict[str, Any]) -> T:
        return self._from_dict(data)

    def load_many(self, items: Iterable[Dict[str, Any]]) -> List[T]:
        return [self._from_dict(each) for each in items]

    def dump(self, o: T) -> Dict[str, Any]:
        return self._dump(o)

    def dump_many(self, items: Collection[T]) -> List[Dict[str, Any]]:
        return [self._dump(o) for o in items]

    def _dump(self, o) -> Dict[str, Any]:
        check_is_instance(o, self.cls)
        return self.serializer.dump(o)

    def _from_dict(self, data: Mapping):
        return self.serializer.load(data)

    def __repr__(self):
        path = class_path(type(self))
        if path == 'serious.dict.api.DictModel':
            path = 'serious.DictModel'
        return f'<{path}[{class_path(self.cls)}] at {hex(id(self))}>'
