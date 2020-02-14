from dataclasses import dataclass
from typing import Dict, Iterable, Tuple, Union

from sebex.analysis.analyzer import AnalysisEntry, AnalysisError
from sebex.analysis.language import Language
from sebex.config import ProjectHandle
from sebex.jobs import for_each
from sebex.log import operation

_Projects = Dict[ProjectHandle, Tuple[Language, AnalysisEntry]]
_PackageNameIndex = Dict[str, ProjectHandle]


@dataclass(eq=False)
class AnalysisDatabase:
    _projects: _Projects
    _package_name_index: _PackageNameIndex

    def projects(self) -> Iterable[ProjectHandle]:
        return self._projects.keys()

    def packages(self) -> Iterable[str]:
        return self._package_name_index.keys()

    def has_project(self, project: ProjectHandle) -> bool:
        return project in self._projects

    def has_package(self, package: str) -> bool:
        return package in self._package_name_index

    def __contains__(self, item: Union[ProjectHandle, str]) -> bool:
        if isinstance(item, ProjectHandle):
            return self.has_project(item)
        elif isinstance(item, str):
            return self.has_package(item)
        else:
            return False

    def language(self, project: ProjectHandle) -> Language:
        return self._projects[project][0]

    def about(self, project: ProjectHandle) -> AnalysisEntry:
        return self._projects[project][1]

    @classmethod
    def collect(cls, projects: Iterable[ProjectHandle]) -> 'AnalysisDatabase':
        projects = list(projects)

        project_info = dict(zip(projects, for_each(projects, cls._do_collect, desc='Analyzing')))

        with operation('Building analysis database'):
            package_name_index = cls._build_package_name_index(project_info)

        return AnalysisDatabase(project_info, package_name_index)

    @staticmethod
    def _do_collect(project: ProjectHandle) -> Tuple[Language, AnalysisEntry]:
        with operation('Analyzing', project):
            language = Language.detect(project)
            entry = language.analyzer(project)
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
