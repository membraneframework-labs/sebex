from typing import Dict, NamedTuple, Iterable

from semver import VersionInfo

from sebex.analysis.language import Language
from sebex.config import ProjectHandle
from sebex.jobs import for_each
from sebex.log import log, success


class AnalysisEntry(NamedTuple):
    language: Language
    version: VersionInfo


class AnalysisDatabase:
    _project_info: Dict[ProjectHandle, AnalysisEntry]

    def __init__(self, repo_info) -> None:
        self._project_info = repo_info

    @classmethod
    def collect(cls, projects: Iterable[ProjectHandle]) -> 'AnalysisDatabase':
        projects = list(projects)
        project_info = dict(zip(projects, for_each(projects, cls._do_collect, desc='Analyzing')))
        return AnalysisDatabase(project_info)

    @staticmethod
    def _do_collect(project: ProjectHandle) -> AnalysisEntry:
        log('Analyzing', project)

        language = Language.detect(project)
        version = language.analyzer.package_version(project)

        success('Analyzed', project)
        return AnalysisEntry(language=language, version=version)
