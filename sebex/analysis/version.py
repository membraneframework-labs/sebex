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

    def truncate(self, version: Version) -> Version:
        if self == self.MAJOR:
            return Version(major=version.major, minor=version.minor, patch=0,
                           prerelease=version.prerelease, build=version.build)
        elif self == self.MINOR:
            return version
        else:
            assert False, 'unreachable'

    @classmethod
    def best_for(cls, dependency_version: Version) -> 'Pin':
        """
        Returns best pin for dependency version requirement (e.g. `~> 1.0`).
        """

        if dependency_version.major > 0 and dependency_version.patch == 0:
            return cls.MAJOR
        else:
            return cls.MINOR

    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)


_SHORT_REGEX = re.compile(
    r"""
        ^
        (?P<major>0|[1-9]\d*)
        \.
        (?P<minor>0|[1-9]\d*)
        (?:-(?P<prerelease>
            (?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)
            (?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*
        ))?
        (?:\+(?P<build>
            [0-9a-zA-Z-]+
            (?:\.[0-9a-zA-Z-]+)*
        ))?
        $
        """,
    re.VERBOSE,
)


# TODO: Support `and` and `or` operators
@dataclass(frozen=True)
class VersionRequirement:
    __slots__ = ['operator', 'base', 'pin']

    operator: VersionOperator
    base: Version
    pin: Pin

    def match(self, version: Version) -> bool:
        pinned_base = self.pin.truncate(self.base)
        pinned_version = self.pin.truncate(version)

        # The requirement will not match a pre-release version
        # unless the operand is a pre-release version.
        if pinned_version.prerelease is not None or pinned_version.build is not None:
            if pinned_base.prerelease is None and pinned_base.build is None:
                return False

        if self.operator == '==':
            return pinned_version == pinned_base
        elif self.operator == '!=':
            return pinned_version != pinned_base
        elif self.operator == '>':
            return pinned_version > pinned_base
        elif self.operator == '<':
            return pinned_version < pinned_base
        elif self.operator == '>=':
            return pinned_version >= pinned_base
        elif self.operator == '<=':
            return pinned_version <= pinned_base
        elif self.operator == '~>':
            if self.pin == Pin.MAJOR:
                next_incompatible = pinned_base.bump_major()
            elif self.pin == Pin.MINOR:
                next_incompatible = pinned_base.bump_minor()
            else:
                assert False, 'unreachable'

            return pinned_base <= pinned_version < next_incompatible
        else:
            assert False, 'unreachable'

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
            return Version(
                major=int(match['major']),
                minor=int(match['minor']),
                patch=0,
                prerelease=match['prerelease'],
                build=match['build'],
            ), Pin.MAJOR

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

    @classmethod
    def targeting(cls, version: Version) -> 'VersionSpec':
        if version.prerelease or version.build:
            operator = VersionOperator('==')
            pin = Pin.MINOR
        else:
            operator = VersionOperator('~>')
            pin = Pin.best_for(version)

        return cls(VersionRequirement(
            operator=operator,
            base=version,
            pin=pin,
        ))


class UnsolvableBump(Exception):
    pass


class Bump(IntEnum):
    """
    Denotes at what degree should the version specification be bumped.

    An ordering is defined, reflecting the degree of the change:

    >>> Bump.STAY_AS_IS < Bump.PATCH < Bump.MINOR < Bump.MAJOR < Bump.UNSOLVABLE
    True
    """

    # TODO Support prerelease & build bumps?

    MAJOR = 3
    MINOR = 2
    PATCH = 1
    STAY_AS_IS = 0
    UNSOLVABLE = 10

    def apply(self, version: Version) -> Version:
        if self == self.UNSOLVABLE:
            raise UnsolvableBump()
        elif self == self.STAY_AS_IS:
            return version
        elif self == self.MAJOR:
            return version.bump_major()
        elif self == self.MINOR:
            return version.bump_minor()
        elif self == self.PATCH:
            return version.bump_patch()
        else:
            assert False, 'unreachable'

    def derive(self, dependency: Version) -> 'Bump':
        """
        Given libraries `A` and `B`, `B` having `A` as dependency. We are releasing `A`:

        1. If we bump *patch* `A` (1.0.0 -> 1.0.1), then we bump *patch* `B` (1.0.0 -> 1.0.1)

            >>> Bump.PATCH.derive(Version.parse('1.0.0'))
            <Bump.PATCH>

        2. If we bump *minor* `A` (1.0.0 -> 1.1.0), then we bump *patch* `B` (1.0.0 -> 1.0.1)

            >>> Bump.MINOR.derive(Version.parse('1.0.0'))
            <Bump.PATCH>

        3. If we bump *major* `A` (1.0.0 -> 2.0.0), then we bump *minor* `B` (1.0.0 -> 1.1.0)

            >>> Bump.MAJOR.derive(Version.parse('1.0.0'))
            <Bump.MINOR>

        4. If we bump *patch* `A` <1.0 (0.1.0 -> 0.1.1), then we bump *patch* `B` (1.0.0 -> 1.0.1)

            >>> Bump.PATCH.derive(Version.parse('0.1.0'))
            <Bump.PATCH>

        5. If we bump *minor* `A` <1.0 (0.1.0 -> 0.2.0), then we bump *minor* `B` (1.0.0 -> 1.1.0)

            >>> Bump.MINOR.derive(Version.parse('0.1.0'))
            <Bump.MINOR>

        6. `STAY_AS_IS` and `UNSOLVABLE` always return themselves

            >>> Bump.STAY_AS_IS.derive(Version.parse('1.0.0'))
            <Bump.STAY_AS_IS>
            >>> Bump.UNSOLVABLE.derive(Version.parse('1.0.0'))
            <Bump.UNSOLVABLE>


        :param dependency: Version of library `A` before bumping.
        :return: Bump value for library `B`.
        """

        if self in [self.UNSOLVABLE, self.STAY_AS_IS]:
            return self
        elif dependency.major == 0:
            if self == self.PATCH:
                return self.PATCH
            elif self == self.MINOR:
                return self.MINOR
        else:
            if self == self.PATCH:
                return self.PATCH
            elif self == self.MINOR:
                return self.PATCH
            elif self == self.MAJOR:
                return self.MINOR

        assert False, 'unreachable'

    @classmethod
    def between(cls, fr: Version, to: Version) -> 'Bump':
        if fr > to:
            return cls.UNSOLVABLE
        elif fr.prerelease is not None or fr.build is not None:
            return cls.UNSOLVABLE
        elif to.prerelease is not None or to.build is not None:
            return cls.UNSOLVABLE
        elif fr == to:
            return cls.STAY_AS_IS
        elif fr.major < to.major:
            return cls.MAJOR
        elif fr.minor < to.minor:
            return cls.MINOR
        else:
            return cls.PATCH

    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)
