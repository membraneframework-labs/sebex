from fnmatch import fnmatch
from typing import List, TypeVar, Type, Set

K = TypeVar('K')


class Pattern:
    def __init__(self, whitelist: List[str], blacklist: Set[str]):
        self._whitelist = whitelist
        self._blacklist = blacklist

    @classmethod
    def compile(cls: Type[K], patterns: List[str]) -> K:
        whitelist = []
        blacklist = set()
        for pattern in patterns:
            if pattern.startswith('!'):
                blacklist.add(pattern[1:])
            else:
                whitelist.append(pattern)

        return cls(whitelist, blacklist)

    def match(self, name: str) -> bool:
        if name in self._blacklist:
            return False

        for pattern in self._whitelist:
            if fnmatch(name, pattern):
                return True

        return False

    def __str__(self) -> str:
        return f'Pattern(whitelist={self._whitelist}, blacklist={list(self._blacklist)})'
