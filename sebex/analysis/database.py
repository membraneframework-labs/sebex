from dataclasses import dataclass
from typing import Dict, Iterable, Tuple, Optional

import click

from sebex.edit.span import Span
from sebex.analysis.version import Version, VersionSpec, VersionRequirement, Pin
from sebex.analysis.model import Language, AnalysisError, AnalysisEntry, Release, Dependency
from sebex.config.manifest import ProjectHandle, RepositoryHandle
from sebex.jobs import for_each
from sebex.language import detect_language, language_support_for, Language
from sebex.log import operation

_Projects = Dict[ProjectHandle, Tuple[Language, AnalysisEntry]]
_PackageNameIndex = Dict[str, ProjectHandle]

_UNKNOWN_LANGUAGE = click.style('UNKNOWN LANGUAGE', fg='yellow')

VIRTUAL_NODE = '__virtual_root_node_project__'
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
        return self._get_project(project)[0]

    def about(self, project: ProjectHandle) -> AnalysisEntry:
        return self._get_project(project)[1]

    def _get_project(self, project):
        if self.has_project(project):
            return self._projects[project]
        else:
            raise AnalysisError(f'Project not found: "{project}". Make sure projects are synced via `sebex sync`.')

    @classmethod
    def collect(cls, projects: Iterable[ProjectHandle], bumps: dict[ProjectHandle, Version]=None) -> 'AnalysisDatabase':
        projects = list(projects)
        projects = zip(projects, for_each(projects, cls._do_collect, desc='Analyzing'))
        # Filter out ignored
        projects = filter(lambda t: t[1][1], projects)
        projects = dict(projects)
        if bumps is not None:
            projects = cls._add_virtual_root(projects, bumps)
        return cls._analyze(projects)

    @classmethod
    def _analyze(cls, projects: _Projects) -> 'AnalysisDatabase':
        with operation('Building analysis database'):
            package_name_index = cls._build_package_name_index(projects)

        return cls(projects, package_name_index)

    @staticmethod
    def _do_collect(project: ProjectHandle) -> Tuple[Language, Optional[AnalysisEntry]]:
        with operation('Analyzing', project) as reporter:
            language = detect_language(project)

            if language is Language.UNKNOWN:
                reporter(_UNKNOWN_LANGUAGE)
                return language, None

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

    @classmethod
    def _add_virtual_root(cls, projects: dict[ProjectHandle], bumps: dict[ProjectHandle, Version]) -> dict[ProjectHandle]:
        # create a fake package `VIRTUAL_NODE` with version 0.1.0
        project = ProjectHandle(RepositoryHandle(VIRTUAL_NODE))
        analysis_entry = AnalysisEntry(
            VIRTUAL_NODE,
            Version(0, 1, 0),
            Span(0, 0, 0, 0),
            [],
            [Release(Version(0, 1, 0))])
        projects[project] = (Language.ELIXIR, analysis_entry)
        # for all packages to be released add a dependency to the virtual package
        # this places it at the root of the dependency graph of all updated packages
        for project, _version in bumps.items():
            _language, analysis_entry = projects[project]
            dependency = Dependency(
                        name=VIRTUAL_NODE, 
                        defined_in=str(project), 
                        version_spec=VersionSpec(
                            value=VersionRequirement(
                                operator='~>', 
                                base=Version(0, 1, 0), 
                                pin=Pin.MINOR)), 
                        version_spec_span=Span(start_line=0, start_column=0, end_line=0, end_column=0))
            analysis_entry.dependencies.append(dependency)
        return projects