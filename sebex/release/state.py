from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from functools import total_ordering
from textwrap import indent
from typing import List, Iterator, Collection, Iterable, Dict

import click

from sebex.analysis import Version, AnalysisDatabase, DependentsGraph, Language
from sebex.analysis.version import Bump, UnsolvableBump
from sebex.checksum import Checksum, Checksumable
from sebex.config import ProjectHandle, ConfigFile
from sebex.config.format import Format, YamlFormat
from sebex.log import operation, error


@total_ordering
class ReleaseStage(Enum):
    CLEAN = 'clean'
    BRANCH_OPENED = 'branch_opened'
    PULL_REQUEST_OPENED = 'pull_request_opened'
    PULL_REQUEST_MERGED = 'pull_request_merged'
    PUBLISHED = 'published'
    DONE = 'done'

    @property
    def human(self) -> str:
        return self.value.replace('_', ' ').upper()

    def describe(self) -> str:
        if self == self.CLEAN:
            return ''
        elif self == self.DONE:
            return click.style(self.human, fg='green', bold=True)
        else:
            return click.style(self.human, fg='blue', bold=True)

    def __iter__(self):
        return iter(s for s in self.__class__ if s > self)

    @property
    def next(self) -> 'ReleaseStage':
        return next(iter(self))

    def __le__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        else:
            for e in self.__class__:
                if e == self:
                    return True
                elif e == other:
                    return False

    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)

    def __str__(self):
        return self.value


@dataclass
class ReleaseState(ConfigFile, Checksumable):
    _name = 'release'

    sources: Dict[ProjectHandle, Version]
    phases: List['PhaseState']

    def __init__(self, name=None, data=None, sources=None, phases=None):
        self.sources = sources
        self.phases = phases

        super().__init__(name, data)

    def _load_data(self, data):
        if data is not None:
            self.sources = {ProjectHandle.parse(p): Version.parse(v)
                            for p, v in data['release'].items()}
            self.phases = [PhaseState.from_raw(p) for p in data['phases']]

    def _make_data(self):
        return {
            'release': {str(p): str(v) for p, v in self.sources.items()},
            'phases': [p.to_raw() for p in self.phases]
        }

    @classmethod
    def format(cls) -> Format:
        return YamlFormat(autogenerated=True)

    def codename(self) -> str:
        return Checksum.of(self).petname

    def has_project(self, project: ProjectHandle) -> bool:
        for phase in self.phases:
            if phase.has_project(project):
                return True

        return False

    def get_project(self, project: ProjectHandle) -> 'ProjectState':
        for phase in self.phases:
            if phase.has_project(project):
                return phase.get_project(project)

        raise KeyError(f'Project {project} is not part of this release.')

    def current_phase(self) -> 'PhaseState':
        for phase in self.phases:
            if not phase.is_done():
                return phase
        else:
            return self.phases[-1]

    def is_clean(self):
        return self.current_phase() == self.phases[0] and self.phases[0].is_clean()

    def is_done(self):
        return self.current_phase() == self.phases[-1] and self.phases[-1].is_done()

    def is_in_progress(self):
        return not self.is_clean() and not self.is_done()

    def describe(self) -> str:
        header = click.style(f'Release "{self.codename()}"', fg="magenta")
        txt = f'{header}\n' \
              f'{click.style("=" * len(click.unstyle(header)), fg="magenta")}\n\n'

        for i, phase in enumerate(self.phases, start=1):
            txt += f'{i}. {phase.describe(self)}'

        return txt

    def checksum(self, hasher):
        hasher(self.sources)
        hasher(self.phases)

    @classmethod
    def plan(cls, project: ProjectHandle, to_version: Version,
             db: AnalysisDatabase, graph: DependentsGraph) -> 'ReleaseState':
        with operation('Constructing release plan'):
            about_project = db.about(project)
            from_version = about_project.version

            if from_version == to_version:
                # We are not releasing anything at all.
                return cls(sources={}, phases=[])
            elif from_version > to_version:
                # We are backporting bug fixes to older releases than the current one.
                raise NotImplementedError('backports are not implemented yet')
            else:
                # We are making a brand-new release
                sources = {project: to_version}

                phases = graph.upgrade_phases(about_project.package)
                phases = (
                    (db.get_project_by_package(pkg) for pkg in sorted(phase))
                    for phase in phases
                )
                phases = [PhaseState.clean(projs, db) for projs in phases]
                assert len(phases) > 0

                rel = cls(sources=sources, phases=phases)

                # Seed the release with initial project
                rel.get_project(project).to_version = to_version

                rel._solve_bumps(db, graph)
                return rel

    def _solve_bumps(self, db: AnalysisDatabase, graph: DependentsGraph):
        """
        Propagate version bumps down the phases, we are searching for
        maximum needed bump for each project.
        """

        bumps = defaultdict(lambda: Bump.STAY_AS_IS)

        for handle in self.sources.keys():
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
                if proj.project in self.sources:
                    proj.to_version = self.sources[proj.project]
                else:
                    proj.to_version = bumps[proj.project].apply(proj.from_version)


@dataclass
class PhaseState(Collection['ProjectReleaseState'], Checksumable):
    _projects: List['ProjectState']

    def __len__(self) -> int:
        return len(self._projects)

    def __iter__(self) -> Iterator['ProjectState']:
        return iter(self._projects)

    def __contains__(self, item) -> bool:
        return item in self._projects

    def is_clean(self):
        return all(p.stage == ReleaseStage.CLEAN for p in self._projects)

    def is_done(self):
        return all(p.stage == ReleaseStage.DONE for p in self._projects)

    def is_in_progress(self):
        return not self.is_clean() and not self.is_done()

    def codename(self) -> str:
        return Checksum.of(self).petname

    def has_project(self, project: ProjectHandle) -> bool:
        for prs in self._projects:
            if prs.project == project:
                return True

        return False

    def get_project(self, project: ProjectHandle) -> 'ProjectState':
        for prs in self._projects:
            if prs.project == project:
                return prs

        raise KeyError(f'This phase does not include project {project}')

    def describe(self, release: ReleaseState) -> str:
        stage = ''
        if self.is_in_progress():
            stage = click.style('IN PROGRESS', fg='blue', bold=True)
        elif self.is_done():
            stage = click.style('DONE', fg='blue', bold=True)

        header = ', '.join([f'Phase "{self.codename()}"', stage])
        txt = f'{header}\n'

        for proj in sorted(self._projects, key=lambda p: p.project):
            descr = '  * ' + indent(proj.describe(release), '    ')[4:]
            txt += f'{descr}\n'

        return txt

    @classmethod
    def clean(cls, projects: Iterable[ProjectHandle], db: AnalysisDatabase) -> 'PhaseState':
        return PhaseState([ProjectState.clean(proj, db) for proj in projects])

    def checksum(self, hasher):
        for p in self._projects:
            hasher(p)

    def to_raw(self) -> Dict:
        return {
            'projects': [p.to_raw() for p in self._projects],
        }

    @classmethod
    def from_raw(cls, o: Dict) -> 'PhaseState':
        return cls([ProjectState.from_raw(p) for p in o['projects']])


@dataclass
class ProjectState(Checksumable):
    project: ProjectHandle
    from_version: Version
    to_version: Version
    language: Language
    stage: ReleaseStage = ReleaseStage.CLEAN

    @property
    def bump(self) -> Bump:
        return Bump.between(self.from_version, self.to_version)

    def describe(self, release: ReleaseState) -> str:
        project_name = str(self.project)

        if self.project in release.sources:
            project_name = click.style(project_name, bold=True)

        from_version = click.style(str(self.from_version), fg="cyan")
        to_version = click.style(str(self.to_version), fg=_bump_color(self.bump))

        return ', '.join([
            f'{project_name}',
            f'{from_version} -> {to_version}',
            self.stage.describe(),
        ])

    @classmethod
    def clean(cls, project: ProjectHandle, db: AnalysisDatabase) -> 'ProjectState':
        about = db.about(project)
        return cls(
            project=project,
            from_version=about.version,
            to_version=about.version,
            language=db.language(project),
        )

    def checksum(self, hasher):
        hasher(self.project)
        hasher(self.from_version)
        hasher(self.to_version)
        hasher(self.language)

    def to_raw(self) -> Dict:
        return {
            'project': str(self.project),
            'from_version': str(self.from_version),
            'to_version': str(self.to_version),
            'language': str(self.language),
            'stage': str(self.stage),
        }

    @classmethod
    def from_raw(cls, o: Dict) -> 'ProjectState':
        return cls(
            project=ProjectHandle.parse(o['project']),
            from_version=Version.parse(o['from_version']),
            to_version=Version.parse(o['to_version']),
            language=Language(o['language']),
            stage=ReleaseStage(o['stage']),
        )


def _bump_color(bump: Bump) -> str:
    if bump in [Bump.STAY_AS_IS, Bump.PATCH]:
        return 'cyan'
    elif bump == Bump.MINOR:
        return 'green'
    elif bump == Bump.MAJOR:
        return 'yellow'
    else:
        return 'red'
