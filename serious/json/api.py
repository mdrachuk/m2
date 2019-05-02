from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional, TypeVar, Type, Generic, List, MutableMapping, Collection

from serious.json.preconditions import _check_that_loading_an_object, _check_that_loading_a_list
from serious.preconditions import _check_isinstance, _check_is_dataclass
from serious.serialization import SeriousSerializer

T = TypeVar('T')


@dataclass(frozen=True)
class Dumping:
    indent: Optional[int] = None
    encoder_options: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Loading:
    allow_missing: bool = False
    allow_unexpected: bool = False
    decoder_options: dict = field(default_factory=dict)


class JsonSchema(Generic[T]):

    def __init__(self, cls: Type[T], load: Loading, dump: Dumping):
        self._cls = _check_is_dataclass(cls)
        self._dump = dump
        self._load = load
        self._serializer = SeriousSerializer(cls, self._load.allow_missing, self._load.allow_unexpected)

    def dump(self, o: T) -> str:
        _check_isinstance(o, self._cls)
        return self._dump_any(self._serializer.dump(o))

    def dump_many(self, items: Collection[T]) -> str:
        dict_items = [self._serializer.dump(_check_isinstance(o, self._cls)) for o in items]
        return self._dump_any(dict_items)

    def load(self, json_: str) -> T:
        data: MutableMapping = json.loads(json_, **self._load.decoder_options)
        _check_that_loading_an_object(data, self._cls)
        return self._from_dict(data)

    def load_many(self, json_: str) -> List[T]:
        data: Collection = json.loads(json_, **self._load.decoder_options)
        _check_that_loading_a_list(data, self._cls)
        return [self._from_dict(each) for each in data]

    def _from_dict(self, data: MutableMapping):
        return self._serializer.load(data)

    def _dump_any(self, dict_items):
        return json.dumps(dict_items,
                          skipkeys=False,
                          ensure_ascii=False,
                          check_circular=True,
                          allow_nan=False,
                          indent=self._dump.indent,
                          separators=None,
                          default=None,
                          sort_keys=False,
                          **self._dump.encoder_options)


def json_schema(cls: Type[T], *,
                allow_missing: bool = Loading.allow_missing,
                allow_unexpected: bool = Loading.allow_unexpected,
                indent: Optional[int] = Dumping.indent) -> JsonSchema[T]:
    dumping = Dumping(indent=indent)
    loading = Loading(allow_missing=allow_missing, allow_unexpected=allow_unexpected)
    return JsonSchema(cls, load=loading, dump=dumping)
