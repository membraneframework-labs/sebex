from dataclasses import dataclass
from typing import List, Iterator, Collection, Iterable

from sebex.analysis import Version, AnalysisDatabase, DependentsGraph
from sebex.config import ProjectHandle
from sebex.log import operation


@dataclass
class ReleaseState:
    phases: List['PhaseState']

    @classmethod
    def plan(cls, project: ProjectHandle, to_version: Version,
             db: AnalysisDatabase, graph: DependentsGraph) -> 'ReleaseState':
        with operation('Constructing release plan'):
            about_project = db.about(project)
            from_version = about_project.version

            if from_version == to_version:
                # We are not releasing anything at all.
                return cls(phases=[])
            elif from_version > to_version:
                # We are backporting bug fixes to older releases than the current one.
                raise NotImplementedError('backports are not implemented yet')
            else:
                # We are making a brand-new release
                phases = graph.upgrade_phases(about_project.package)
                phases = (
                    (db.get_project_by_package(pkg) for pkg in sorted(phase))
                    for phase in phases
                )
                phases = [PhaseState.clean(projs, db) for projs in phases]
                assert len(phases) > 0

                phases[0].get_by_project(project).to_version = to_version

                return cls(phases=phases)


@dataclass
class PhaseState(Collection['ProjectReleaseState']):
    _items: List['ProjectReleaseState']

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator['ProjectReleaseState']:
        return iter(self._items)

    def __contains__(self, item) -> bool:
        return item in self._items

    def has_project(self, project: ProjectHandle) -> bool:
        for prs in self._items:
            if prs.project == project:
                return True

        return False

    def get_by_project(self, project: ProjectHandle) -> 'ProjectReleaseState':
        for prs in self._items:
            if prs.project == project:
                return prs

        raise KeyError(f'This phase does not include project {project}')

    @classmethod
    def clean(cls, projects: Iterable[ProjectHandle], db: AnalysisDatabase) -> 'PhaseState':
        return PhaseState([ProjectReleaseState.clean(proj, db) for proj in projects])


@dataclass
class ProjectReleaseState:
    project: ProjectHandle
    from_version: Version
    to_version: Version

    @classmethod
    def clean(cls, project: ProjectHandle, db: AnalysisDatabase) -> 'ProjectReleaseState':
        about = db.about(project)
        return cls(
            project=project,
            from_version=about.version,
            to_version=about.version
        )
