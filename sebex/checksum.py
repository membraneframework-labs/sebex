import hashlib
from abc import ABC, abstractmethod
from random import Random
from typing import Callable, Any

import petname


class Checksum:
    digest: str

    def __init__(self, digest: str):
        self.digest = digest

    @property
    def numeric(self) -> int:
        return int(self.digest, 16)

    @property
    def petname(self) -> str:
        return _deterministic_petname(self.numeric).title()

    def __eq__(self, other):
        if isinstance(other, Checksum):
            return self.digest == other.digest

        return False

    def __hash__(self):
        return hash(self.digest)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.digest})'

    def __str__(self) -> str:
        return self.digest

    @classmethod
    def of(cls, o: Any) -> 'Checksum':
        m = hashlib.sha1()

        def visit(x):
            if isinstance(x, Checksumable):
                x.checksum(visit)
            elif isinstance(x, dict):
                for k, v in x.items():
                    visit(k)
                    visit(v)
            elif isinstance(x, str):
                m.update(bytes(x, 'utf-8'))
            elif isinstance(x, bytes):
                m.update(x)
            elif is_iterable(x):
                for e in x:
                    visit(e)
            else:
                m.update(bytes(repr(x), 'utf-8'))

        visit(o)

        return cls(m.hexdigest())


class Checksumable(ABC):
    @abstractmethod
    def checksum(self, hasher: Callable[[Any], None]) -> None: ...


def is_iterable(obj) -> bool:
    try:
        iter(obj)
        return True
    except TypeError:
        return False


def _adverb(rnd, letters=6):
    while 1:
        w = rnd.choice(petname.adverbs)
        if len(w) <= letters:
            return w


def _adjective(rnd, letters=6):
    while 1:
        w = rnd.choice(petname.adjectives)
        if len(w) <= letters:
            return w


def _name(rnd, letters=6):
    while 1:
        w = rnd.choice(petname.names)
        if len(w) <= letters:
            return w


def _deterministic_petname(seed: int, letters=6) -> str:
    rnd = Random(seed)
    return f'{_adverb(rnd, letters)} {_adjective(rnd, letters)} {_name(rnd, letters)}'
