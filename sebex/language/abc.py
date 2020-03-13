from abc import ABC, abstractmethod
from typing import List

from sebex.analysis.model import Language, AnalysisEntry, DependencyUpdate
from sebex.analysis.version import Version
from sebex.config.manifest import ProjectHandle
from sebex.edit.span import Span


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
    def write_release(self, project: ProjectHandle, to_version: Version, to_version_span: Span,
                      dependency_updates: List[DependencyUpdate]): ...
