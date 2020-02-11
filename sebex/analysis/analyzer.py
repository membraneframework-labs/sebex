from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from semver import VersionInfo

if TYPE_CHECKING:
    from sebex.config import ProjectHandle


class AnalysisError(Exception):
    pass


class Analyzer(ABC):
    @abstractmethod
    def package_version(self, project: 'ProjectHandle') -> VersionInfo:
        pass
