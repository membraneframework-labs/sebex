from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List

from sebex.analysis.version import Version, VersionSpec
from sebex.config import ProjectHandle
from sebex.edit import Span


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
    version_lock: Optional[Version] = None

    def version_str(self):
        result = str(self.version_spec.value)
        if self.version_lock is not None:
            result += f' (locked at {self.version_lock})'
        return result


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
        return bool(self.releases)


@dataclass
class DependencyUpdate:
    package: str
    to_spec: VersionSpec
    to_spec_span: Span


class LanguageSupport(ABC):
    @classmethod
    @abstractmethod
    def language(cls) -> Language: ...

    @classmethod
    @abstractmethod
    def test_project(cls, project: ProjectHandle) -> bool: ...

    @abstractmethod
    def analyze(self, project: ProjectHandle) -> AnalysisEntry: ...

    @abstractmethod
    def write_release(self, to_version: Version, to_version_span: Span,
                      dependency_updates: List[DependencyUpdate]): ...
