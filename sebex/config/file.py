from contextlib import contextmanager
from copy import deepcopy
from typing import Type, TypeVar, Optional

from sebex.config.format import Format, YamlFormat

K = TypeVar('K', bound='ConfigFile')


class ConfigFile:
    _name: str = None
    _data = None

    def __init__(self, name: Optional[str], data):
        if name is not None:
            self._name = name

        self._load_data(data)

    def _load_data(self, data):
        self._data = merge_defaults(data, self._data)

    def _make_data(self):
        return self._data

    @classmethod
    def format(cls) -> Format:
        return YamlFormat()

    @classmethod
    def exists(cls, name: str = None) -> bool:
        name = cls._get_name(name)
        full_path = cls.format().full_path(name)
        return full_path.exists()

    @classmethod
    def open(cls: Type[K], name: str = None) -> 'K':
        name = cls._get_name(name)
        full_path = cls.format().full_path(name)

        if full_path.exists():
            with open(full_path, 'r') as f:
                data = cls.format().load(f)
        else:
            data = None

        return cls(name=name, data=data)

    def save(self) -> None:
        with open(self.format().full_path(self._name), 'w') as f:
            self.format().dump(self._make_data(), f)

    def delete(self):
        full_path = self.format().full_path(self._name)
        full_path.unlink()

    @contextmanager
    def transaction(self: K):
        try:
            yield self
        finally:
            self.save()

    @classmethod
    def _get_name(cls, name):
        if name is None:
            name = cls._name

        if name is None:
            raise ValueError('Unknown config file name')

        return name


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
