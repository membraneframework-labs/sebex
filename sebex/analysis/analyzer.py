from dataclasses import dataclass, field
from typing import Callable, Optional, List

from sebex.analysis.version import Version, VersionSpec
from sebex.config import ProjectHandle
from sebex.edit import Span


class AnalysisError(Exception):
    pass


@dataclass(order=True, frozen=True)
class Dependency:
    name: str
    version_spec: VersionSpec
    version_spec_span: Span
    version_lock: Optional[Version] = None

    def version_str(self):
        result = str(self.version_spec.value)
        if self.version_lock is not None:
            result += f' (locked at {self.version_lock})'
        return result


@dataclass
class AnalysisEntry:
    package: str
    version: Version
    version_span: Span
    dependencies: List[Dependency] = field(default_factory=list)


Analyzer = Callable[[ProjectHandle], AnalysisEntry]
