from typing import NamedTuple, Callable, Optional, List

from sebex.analysis.version import Version, VersionSpec
from sebex.config import ProjectHandle
from sebex.edit import Span


class AnalysisError(Exception):
    pass


class Dependency(NamedTuple):
    name: str
    version_spec: VersionSpec
    version_spec_span: Span
    version_lock: Optional[Version] = None

    def version_str(self):
        result = str(self.version_spec.value)
        if self.version_lock is not None:
            result += f' (locked at {self.version_lock})'
        return result


class AnalysisEntry(NamedTuple):
    package: str
    version: Version
    version_span: Span
    dependencies: List[Dependency] = []


Analyzer = Callable[[ProjectHandle], AnalysisEntry]
