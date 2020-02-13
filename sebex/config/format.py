import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TextIO

import yaml

from sebex.context import Context


class Format(ABC):
    @classmethod
    @abstractmethod
    def ext(cls) -> str:
        ...

    @classmethod
    @abstractmethod
    def load(cls, fp: TextIO):
        ...

    @classmethod
    @abstractmethod
    def dump(cls, data, fp: TextIO):
        ...

    @classmethod
    def full_path(cls, name: str) -> Path:
        full_path = Context.current().meta_path / name
        full_path = full_path.with_suffix(cls.ext())
        return full_path


class JsonFormat(Format):
    @classmethod
    def ext(cls) -> str:
        return '.json'

    @classmethod
    def load(cls, fp: TextIO):
        return json.load(fp)

    @classmethod
    def dump(cls, data, fp: TextIO):
        json.dump(data, fp, indent=2)


class YamlFormat(Format):
    @classmethod
    def ext(cls) -> str:
        return '.yaml'

    @classmethod
    def load(cls, fp: TextIO):
        return yaml.safe_load(fp)

    @classmethod
    def dump(cls, data, fp: TextIO):
        yaml.dump(data, fp)


class LinesFormat(Format):
    COMMENT = '#'

    @classmethod
    def ext(cls) -> str:
        return '.txt'

    @classmethod
    def load(cls, fp: TextIO):
        any_lines = (any_line.strip() for any_line in fp)
        return [line for line in any_lines if line and not line.startswith(cls.COMMENT)]

    @classmethod
    def dump(cls, data, fp: TextIO):
        if not isinstance(data, list):
            raise Exception('LinesFormat support only lists of strings as data type')

        fp.writelines(f'{str(entry).strip()}\n' for entry in data)
