from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

from sebex.analysis.model import Language, AnalysisError, AnalysisEntry
from sebex.config.manifest import ProjectHandle
from sebex.jobs import for_each
from sebex.language import detect_language, language_support_for
from sebex.log import operation

_Projects = Dict[ProjectHandle, Tuple[Language, AnalysisEntry]]
_PackageNameIndex = Dict[str, ProjectHandle]


@dataclass(eq=False)
class AnalysisDatabase:
    _projects: _Projects
    _package_name_index: _PackageNameIndex

    def projects(self) -> Iterable[ProjectHandle]:
        return self._projects.keys()

    def managed_packages(self) -> Iterable[str]:
        return self._package_name_index.keys()

    def has_project(self, project: ProjectHandle) -> bool:
        return project in self._projects

    def is_package_managed(self, package: str) -> bool:
        return package in self._package_name_index

    def get_project_by_package(self, package: str) -> ProjectHandle:
        return self._package_name_index[package]

    def language(self, project: ProjectHandle) -> Language:
        return self._projects[project][0]

    def about(self, project: ProjectHandle) -> AnalysisEntry:
        return self._projects[project][1]

    @classmethod
    def collect(cls, projects: Iterable[ProjectHandle]) -> 'AnalysisDatabase':
        projects = list(projects)
        projects = dict(zip(projects, for_each(projects, cls._do_collect, desc='Analyzing')))
        return cls._analyze(projects)

    @classmethod
    def _analyze(cls, projects: _Projects) -> 'AnalysisDatabase':
        with operation('Building analysis database'):
            package_name_index = cls._build_package_name_index(projects)

        return cls(projects, package_name_index)

    @staticmethod
    def _do_collect(project: ProjectHandle) -> Tuple[Language, AnalysisEntry]:
        with operation('Analyzing', project):
            language = detect_language(project)
            support = language_support_for(language)
            entry = support.analyze(project)
            return language, entry

    @classmethod
    def _build_package_name_index(cls, projects: _Projects) -> _PackageNameIndex:
        index = dict()
        for project, (_, entry) in projects.items():
            if entry.package not in index:
                index[entry.package] = project
            else:
                raise AnalysisError(f'Duplicate package name: "{entry.package}"')
        return index
