from typing import NamedTuple, Callable

from semver import VersionInfo

from sebex.config import ProjectHandle
from sebex.edit import Span


class AnalysisError(Exception):
    pass


class AnalysisEntry(NamedTuple):
    version: VersionInfo
    version_span: Span


Analyzer = Callable[[ProjectHandle], AnalysisEntry]
