from typing import NamedTuple, Callable, Union, Dict, List, Optional

from semver import VersionInfo

from sebex.config import ProjectHandle
from sebex.edit import Span


class AnalysisError(Exception):
    pass


class Dependency(NamedTuple):
    name: str
    version_spec: Union[str, Dict]
    version_spec_span: Span
    version_lock: Optional[VersionInfo]


class AnalysisEntry(NamedTuple):
    version: VersionInfo
    version_span: Span
    dependencies: List[Dependency]


Analyzer = Callable[[ProjectHandle], AnalysisEntry]
