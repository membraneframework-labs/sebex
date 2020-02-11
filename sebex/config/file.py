from contextlib import contextmanager
from copy import deepcopy
from typing import Type, TypeVar, Union

from sebex.config.format import Format, JsonFormat

K = TypeVar('K', bound='ConfigFile')


class ConfigFile:
    _name: str = None
    _data = None

    def __init__(self, name: Union[str, None], data):
        if name is not None:
            self._name = name

        self._data = merge_defaults(data, self._data)

    @classmethod
    def format(cls) -> Type[Format]:
        return JsonFormat

    @classmethod
    def open(cls: Type[K], name: str = None) -> 'K':
        if name is None:
            name = cls._name

        if name is None:
            raise Exception('Unknown config file name')

        full_path = cls.format().full_path(name)

        if full_path.exists():
            with open(full_path, 'r') as f:
                data = cls.format().load(f)
        else:
            data = None

        return cls(name, data)

    def save(self) -> None:
        with open(self.format().full_path(self._name), 'w') as f:
            self.format().dump(self._data, f)

    @contextmanager
    def transaction(self: K):
        try:
            yield self
        finally:
            self.save()


def merge_defaults(base, defaults):
    return merge_defaults_inner(base, defaults) if base is not None else defaults


def merge_defaults_inner(base, defaults):
    if not isinstance(base, dict):
        return base

    if isinstance(defaults, dict):
        for k, v in defaults.items():
            if k in base and isinstance(base[k], dict) and isinstance(defaults[k], dict):
                merge_defaults_inner(base[k], defaults[k])
            elif k not in base:
                base[k] = deepcopy(defaults[k])

    return base
