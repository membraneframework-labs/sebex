import re
from dataclasses import dataclass
from enum import IntEnum
from typing import Tuple, NewType, Set, Union, Dict, Optional

import semver

# We are aliasing VersionInfo class from SemVer because although it seems to work for our
# use cases right now, it does not mean the Elixir team will make some changes in versioning, or
# we will decide to support other technologies with non-semver versioning scheme.
#
# As a future-proof this should mitigate thinking about relying on semver package in our code.
Version = semver.VersionInfo

VersionOperator = NewType('VersionOperator', str)
VERSION_OPERATORS: Set[VersionOperator] = {VersionOperator(o) for o in
                                           ['==', '!=', '>', '<', '>=', '<=', '~>']}


class Pin(IntEnum):
    """
    Denotes until which part of the base version should version requirement match exactly.

    Possible values:
     - `MAJOR`, which means major release, for example `~> 2.1` and will pin to versions `2.x.x`
     - `MINOR`, minor release, `~> 2.1.2` pins to `2.1.x and >= 2.1.2`

    An ordering is defined, reflecting how much specific the pin is:

    >>> Pin.MINOR < Pin.MAJOR
    True
    """

    MAJOR = 1
    MINOR = 0

    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)


_SHORT_REGEX = re.compile(
    r'^(?P<major>(?:0|[1-9][0-9]*))\.(?P<minor>(?:0|[1-9][0-9]*))$',
    re.VERBOSE
)


# TODO: Support `and` and `or` operators
@dataclass(frozen=True)
class VersionRequirement:
    __slots__ = ['operator', 'base', 'pin']

    operator: VersionOperator
    base: Version
    pin: Pin

    @classmethod
    def parse(cls, req_str: str) -> 'VersionRequirement':
        try:
            operator, base_str = cls._parse_operator(req_str)
            base, pin = cls._parse_base(base_str)
            return VersionRequirement(operator=operator, base=base, pin=pin)
        except ValueError:
            raise ValueError(f'Failed to parse version spec "{req_str}".')

    @classmethod
    def _parse_operator(cls, req_str: str) -> Tuple[VersionOperator, str]:
        for length in [2, 1]:
            for operator in (o for o in VERSION_OPERATORS if len(o) == length):
                if req_str.startswith(operator):
                    return operator, req_str[length:].lstrip()

        return VersionOperator('=='), req_str

    @classmethod
    def _parse_base(cls, base_str: str) -> Tuple[Version, Pin]:
        match = _SHORT_REGEX.match(base_str)
        if match:
            return Version(int(match['major']), int(match['minor']), 0), Pin.MAJOR

        return Version.parse(base_str), Pin.MINOR

    def __str__(self):
        if self.pin == Pin.MAJOR:
            base_str = f'{self.base.major}.{self.base.minor}'
        elif self.pin == Pin.MINOR:
            base_str = str(self.base)
        else:
            assert False, 'unreachable'

        return f'{self.operator} {base_str}'


@dataclass(frozen=True)
class GitRequirement:
    uri: str
    is_github: bool
    ref: Optional[str] = None
    branch: Optional[str] = None
    tag: Optional[str] = None
    submodules: bool = False
    sparse: bool = False

    @classmethod
    def from_dict(cls, raw: Dict) -> 'GitRequirement':
        if 'github' in raw:
            uri = raw['github']
            is_github = True
        else:
            uri = raw['git']
            is_github = False

        return cls(
            uri=uri,
            is_github=is_github,
            ref=raw.get('ref'),
            branch=raw.get('branch'),
            tag=raw.get('tag'),
            submodules=raw.get('submodules', False),
            sparse=raw.get('sparse', False),
        )


@dataclass(frozen=True)
class PathRequirement:
    path: str

    @classmethod
    def from_dict(cls, raw: Dict) -> 'PathRequirement':
        return cls(raw['path'])


@dataclass(frozen=True)
class VersionSpec:
    __slots__ = ['value']

    value: Union[VersionRequirement, GitRequirement, PathRequirement]

    @property
    def is_version(self) -> bool:
        return isinstance(self.value, VersionRequirement)

    @property
    def is_external(self) -> bool:
        return isinstance(self.value, GitRequirement) or isinstance(self.value, PathRequirement)

    @classmethod
    def parse(cls, raw) -> 'VersionSpec':
        if isinstance(raw, str):
            return cls(VersionRequirement.parse(raw))

        if isinstance(raw, dict):
            if 'path' in raw:
                return cls(PathRequirement.from_dict(raw))
            if 'git' in raw or 'github' in raw:
                return cls(GitRequirement.from_dict(raw))

        raise ValueError(f'Unable to parse version spec: {raw!r}')
