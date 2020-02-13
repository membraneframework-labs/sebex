import re
from dataclasses import dataclass
from typing import Tuple, NewType, Set, Union, Dict

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

Pin = NewType('Pin', int)
'''
Denotes until which part of the base version should version requirement match exactly.

Possible values:
 - `0`, which means major release, for example `~> 2.1` and will pin to versions `2.x.x`
 - `1`, minor release, `~> 2.1.2` pins to `2.1.x`
'''

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
            return Version(major=int(match['major']), minor=int(match['minor']), patch=0), Pin(0)

        return Version.parse(base_str), Pin(1)


@dataclass(frozen=True)
class VersionSpec:
    __slots__ = ['value']

    value: Union[VersionRequirement, Dict]

    @property
    def is_version(self) -> bool:
        return isinstance(self.value, VersionRequirement)

    @property
    def is_external(self) -> bool:
        return isinstance(self.value, dict)

    @classmethod
    def parse(cls, raw) -> 'VersionSpec':
        if isinstance(raw, str):
            return cls(VersionRequirement.parse(raw))
        elif isinstance(raw, dict):
            return cls(raw)
        else:
            raise ValueError(f'Unable to parse version spec: {repr(raw)}')
