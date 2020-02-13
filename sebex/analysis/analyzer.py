from typing import NamedTuple, Callable, Dict, Optional

from sebex.analysis.version import Version, VersionSpec
from sebex.config import ProjectHandle
from sebex.edit import Span


class AnalysisError(Exception):
    pass


class Dependency(NamedTuple):
    name: str
    version_spec: VersionSpec
    version_spec_span: Span
    version_lock: Optional[Version]


class AnalysisEntry(NamedTuple):
    version: Version
    version_span: Span
    dependencies: Dict[str, Dependency]


Analyzer = Callable[[ProjectHandle], AnalysisEntry]
