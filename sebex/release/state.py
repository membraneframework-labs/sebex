from collections import defaultdict
from dataclasses import dataclass
from typing import List, Iterator, Collection, Iterable
from textwrap import indent, dedent

from sebex.analysis import Version, VersionSpec, AnalysisDatabase, DependentsGraph
from sebex.analysis.version import Bump, UnsolvableBump
from sebex.checksum import Checksum
from sebex.config import ProjectHandle
from sebex.log import operation, error


@dataclass
class ReleaseState:
    phases: List['PhaseState']

    def has_project(self, project: ProjectHandle) -> bool:
        for phase in self.phases:
            if phase.has_project(project):
                return True

        return False

    def get_project(self, project: ProjectHandle) -> 'ProjectReleaseState':
        for phase in self.phases:
            if phase.has_project(project):
                return phase.get_project(project)

        raise KeyError(f'Project {project} is not part of this release.')

    def describe(self) -> str:
        codename = Checksum.of(self).petname
        header = f'Release "{codename}"'
        txt = f'{header}\n{"=" * len(header)}\n\n'

        for i, phase in enumerate(self.phases, start=1):
            txt += f'{i}. {phase.describe()}'

        return txt

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

                rel = cls(phases=phases)

                # Seed the release with initial project
                rel.get_project(project).to_version = to_version

                rel._solve_bumps([project], db, graph)
                return rel

    def _solve_bumps(self, seeds: Collection[ProjectHandle],
                     db: AnalysisDatabase, graph: DependentsGraph):
        """
        Propagate version bumps down the phases, we are searching for
        maximum needed bump for each project.

        :param seeds: A collection of projects that should not be bumped.
        """

        bumps = defaultdict(lambda: Bump.STAY_AS_IS)

        for handle in seeds:
            project = self.get_project(handle)
            bumps[handle] = Bump.between(project.from_version, project.to_version)
            assert bumps[handle] != Bump.STAY_AS_IS

        for phase in self.phases:
            for proj in phase:
                for dep_pkg in graph.dependents_of(db.about(proj.project).package):
                    dep = db.get_project_by_package(dep_pkg)
                    dep_bump = bumps[proj.project].derive(proj.from_version)
                    bumps[dep] = max(bumps[dep], dep_bump)

        # Verify that all bumps are possible
        invalid_bumps = False
        for project, bump in bumps.items():
            if bump == Bump.UNSOLVABLE:
                error('Unable to bump project', project)
                invalid_bumps = True
        if invalid_bumps:
            raise UnsolvableBump()

        # Apply found version bumps to projects
        for phase in self.phases:
            for proj in phase:
                proj.to_version = bumps[proj.project].apply(proj.from_version)


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

    def get_project(self, project: ProjectHandle) -> 'ProjectReleaseState':
        for prs in self._items:
            if prs.project == project:
                return prs

        raise KeyError(f'This phase does not include project {project}')

    def describe(self) -> str:
        codename = Checksum.of(self).petname
        header = f'Phase "{codename}"'
        txt = f'{header}\n'

        for proj in sorted(self._items, key=lambda p: p.project):
            descr = '  * ' + indent(proj.describe(), '    ')[4:]
            txt += f'{descr}\n'

        return txt

    @classmethod
    def clean(cls, projects: Iterable[ProjectHandle], db: AnalysisDatabase) -> 'PhaseState':
        return PhaseState([ProjectReleaseState.clean(proj, db) for proj in projects])


@dataclass
class ProjectReleaseState:
    project: ProjectHandle
    from_version: Version
    to_version: Version

    def describe(self) -> str:
        spec = VersionSpec.targeting(self.to_version)
        return dedent(f'''\
        {self.project}
        {self.from_version} -> {self.to_version} ({spec})
        ''')

    @classmethod
    def clean(cls, project: ProjectHandle, db: AnalysisDatabase) -> 'ProjectReleaseState':
        about = db.about(project)
        return cls(
            project=project,
            from_version=about.version,
            to_version=about.version
        )
