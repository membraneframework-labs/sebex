from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict

from sebex.analysis.version import Version, VersionSpec
from sebex.edit.span import Span


class Language(Enum):
    ELIXIR = 'elixir'
    UNKNOWN = 'unknown'

    def __str__(self):
        return self.value


class AnalysisError(Exception):
    pass


@dataclass(order=True, frozen=True)
class Dependency:
    name: str
    defined_in: str
    version_spec: VersionSpec
    version_spec_span: Span

    def version_str(self):
        return str(self.version_spec.value)

    def prepare_update(self, to_spec: VersionSpec) -> 'DependencyUpdate':
        return DependencyUpdate(
            name=self.name,
            from_spec=self.version_spec,
            to_spec=to_spec,
            to_spec_span=self.version_spec_span,
        )


@dataclass(order=True, frozen=True)
class Release:
    version: Version
    retired: bool = False


@dataclass
class AnalysisEntry:
    package: str
    version: Version
    version_span: Span
    dependencies: List[Dependency] = field(default_factory=list)
    releases: List[Release] = field(default_factory=list)

    @property
    def is_published(self) -> bool:
        # always publish test packages
        return bool(self.releases) or 'sebex_test' in self.package


@dataclass
class DependencyUpdate:
    name: str
    from_spec: VersionSpec
    to_spec: VersionSpec
    to_spec_span: Span

    def to_raw(self) -> Dict:
        return {
            'name': self.name,
            'from_spec': self.from_spec.to_raw(),
            'to_spec': self.to_spec.to_raw(),
            'to_spec_span': self.to_spec_span.to_raw(),
        }

    @classmethod
    def from_raw(cls, raw: Dict) -> 'DependencyUpdate':
        return DependencyUpdate(
            name=raw['name'],
            from_spec=VersionSpec.from_raw(raw['from_spec']),
            to_spec=VersionSpec.from_raw(raw['to_spec']),
            to_spec_span=Span.from_raw(raw['to_spec_span']),
        )
