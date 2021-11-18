from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from functools import total_ordering
from textwrap import indent
from typing import List, Iterator, Collection, Iterable, Dict, Tuple, Set

import click

from sebex.analysis.database import AnalysisDatabase
from sebex.analysis.graph import DependentsGraph
from sebex.analysis.model import Dependency, Language, DependencyUpdate
from sebex.analysis.version import Bump, VersionRequirement, VersionSpec, Version, UnsolvableBump
from sebex.checksum import Checksum, Checksumable
from sebex.config.file import ConfigFile
from sebex.config.format import Format, YamlFormat
from sebex.config.manifest import Manifest, ProjectHandle
from sebex.edit.span import Span
from sebex.log import operation, error, warn, success


@total_ordering
class ReleaseStage(Enum):
    CLEAN = 'clean'
    BRANCH_OPENED = 'branch_opened'
    PULL_REQUEST_OPENED = 'pull_request_opened'
    PULL_REQUEST_MERGED = 'pull_request_merged'
    BRANCH_CLOSED = 'branch_closed'
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
    def plan(cls, sources: Dict[ProjectHandle, Version], db: AnalysisDatabase, graph: DependentsGraph, update_obsolete: bool) -> 'ReleaseState':
        with operation('Constructing release plan'):
            ignore = set()
            allPhases = []

            for project, to_version in sources.items():
                about_project = db.about(project)
                from_version = about_project.version

                if from_version > to_version:
                    # We are backporting bug fixes to older releases than the current one.
                    raise NotImplementedError('backports are not implemented yet')

                phases = graph.upgrade_phases(about_project.package)
                phases = (
                    (db.get_project_by_package(pkg) for pkg in sorted(phase))
                    for phase in phases
                )
                phases = [PhaseState.clean(projs, db) for projs in phases]
                assert len(phases) > 0
                for phase in phases:
                    allPhases.append(phase)

            rel = cls(sources=sources, phases=allPhases)

            for project, to_version in sources.items():
                # Seed the release with initial project
                rel.get_project(project).to_version = to_version

                # If we are releasing already manually released source version,
                # then simulate brand new release to bump its dependencies
                if from_version == to_version:
                    rel.get_project(project).from_version = _previous_version(to_version)
                    ignore.add(project)

            rel._build_plan(db, graph, update_obsolete)
            # modify the final release plan so that all mentions of `VIRTUAL_ROOT` are removed
            rel._prune_unchanged(ignore=ignore)
            return rel

    def _build_plan(self, db: AnalysisDatabase, graph: DependentsGraph, update_obsolete: bool):
        """
        Propagates version bumps down the phases, we are searching for
        maximum needed bump for each project. Fills `dependency_updates` fields in project states.
        """

        # We will track the minimal version bump needed for each project
        bumps = defaultdict(lambda: Bump.STAY_AS_IS)
        dependency_updates = defaultdict(lambda: [])
        obsolete_pkg_updates = {}

        # Seed bumps with source projects
        for handle in self.sources.keys():
            project = self.get_project(handle)
            bumps[handle] = Bump.between(project.from_version, project.to_version)
        
        projects = {project.project: project for phase in self.phases for project in phase}

        # Here we go
        for project, dependency, relation in self._dependency_relations(db, graph):
            # Don't bump nor update dependencies of prerelease packages (alpha etc.)
            if projects[dependency].from_version._prerelease is not None:
                continue
            # We need to handle each dependency kind (version req, git, path) separately
            if relation.version_spec.is_version:
                req: VersionRequirement = relation.version_spec.value
                # We have to release a new version of dependent if its relation
                # points to soon-to-be-outdated version of the dependency.
                release_new_version = ((req.match(project.from_version) or req.match(_previous_version(project.to_version))) and not req.match(project.to_version))
                dependent_is_obsolete = not req.match(project.from_version) and not req.match(project.to_version)
                if dependent_is_obsolete and dependency not in obsolete_pkg_updates.keys():
                    obsolete_pkg_updates[dependency] = False
                # Obsolete packages that are not directly dependent on a bumped package should be ignored
                ignore_dependent = bumps[project.project] == Bump.STAY_AS_IS
                update_dependent = update_obsolete and dependent_is_obsolete and not ignore_dependent
                if update_dependent:
                    obsolete_pkg_updates[dependency] = True

                if release_new_version or update_dependent:
                    # if a dependency of the package changed it's MINOR or MAJOR version then bump dependent by MINOR
                    req_bump = Bump.MINOR if update_dependent else Bump.STAY_AS_IS
                    version_bump = Bump.between(project.from_version, project.to_version)
                    bumps[dependency] = max(req_bump, version_bump)

                    update = relation.prepare_update(VersionSpec.targeting(project.to_version))
                    dependency_updates[dependency].append(update)

                    # Apply version bump to the dependent project:
                    dependent_project = projects[dependency]
                    if dependency in self.sources:
                        dependent_project.to_version = self.sources[dependency]
                    else:
                        dependent_project.to_version = bumps[dependency].apply(dependent_project.from_version)

                if dependent_is_obsolete:
                    warn(f'Project {dependency} depends on an obsolete version '
                         f'of {project.project} (current version is {project.to_version}, '
                         f'while dependency requirement is {req}).')
            else:
                # TODO Implement handling Git & Path deps
                warn('Project', dependency, 'depends on', project.project,
                     'using git or path requirement, ignoring.')

        for package, will_be_updated in obsolete_pkg_updates.items():
            if will_be_updated:
                success(f'{package} obsolete dependencies will be updated')
            else:
                # either the package was not directly affected by the current release or the `--no-update` flag was set
                warn(f'{package} will not be updated')

        # Verify that all bumps are possible
        invalid_bumps = False
        for project, bump in bumps.items():
            if bump == Bump.UNSOLVABLE:
                error('Unable to bump project', project)
                invalid_bumps = True
        if invalid_bumps:
            raise UnsolvableBump()

        # Sort dependency updates by package names for testability
        for lst in dependency_updates.values():
            lst.sort(key=lambda u: u.name)

        # Apply dependency updates
        for project in projects.values():
            project.dependency_updates = dependency_updates[project.project]

    def _dependency_relations(
        self,
        db: AnalysisDatabase,
        graph: DependentsGraph
    ) -> Iterator[Tuple['ProjectState', ProjectHandle, Dependency]]:
        """
        Visits each project, in dependency-to-dependents order and yields tuples containing:
        dependency release state, dependent handle, dependency relation details.
        """

        # Visit each project, in dependency-to-dependents order
        for phase in self.phases:
            for project in phase:
                project_pkg = db.about(project.project).package

                # Now for each project, get its dependents along with relations...
                for dependency_pkg, relations in graph.dependents_of(project_pkg).items():
                    dependency = db.get_project_by_package(dependency_pkg)

                    # ...and find the dependency relation that connects these two directly.
                    # There should be only one relation in the list, this condition works as an
                    # assertion.
                    relation = next(c for c in relations if c.name == project_pkg)

                    yield project, dependency, relation

    def _prune_unchanged(self, ignore: Set[ProjectHandle] = None):
        """Drop no-op phases."""
        if ignore is None:
            ignore = set()

        pruned_phases = (
            PhaseState([
                project
                for project in phase
                if not self._is_project_noop(project) and project.project not in ignore])
            for phase in self.phases
        )
        self.phases = [phase for phase in pruned_phases if phase]

    @classmethod
    def _is_project_noop(cls, project: 'ProjectState') -> bool:
        if project.from_version == project.to_version:
            return True
        else:
            return False
            

@dataclass
class PhaseState(Collection['ProjectReleaseState'], Checksumable):
    _projects: List['ProjectState']

    def __len__(self) -> int:
        return len(self._projects)

    def __iter__(self) -> Iterator['ProjectState']:
        return iter(self._projects)

    def __contains__(self, item) -> bool:
        return item in self._projects

    def __bool__(self):
        return bool(self._projects)

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
        header = [f'Phase "{self.codename()}"']

        if self.is_in_progress():
            header.append(click.style('IN PROGRESS', fg='blue', bold=True))
        elif self.is_done():
            header.append(click.style('DONE', fg='blue', bold=True))

        header = ', '.join(header)
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
    version_span: Span
    language: Language
    publish: bool = False
    dependency_updates: List[DependencyUpdate] = field(default_factory=list)
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

        headline = [
            f'{project_name}',
            f'{from_version} -> {to_version}',
        ]

        if self.publish:
            headline.append('publish')

        if self.stage.describe():
            headline.append(self.stage.describe())

        headline = ', '.join(headline)

        lines = [headline]

        if self.dependency_updates:
            updates = [
                f'{u.name}, "{u.from_spec}" -> "{u.to_spec}"'
                for u in self.dependency_updates
            ]
            if len(updates) == 1:
                updates = updates[0]
            else:
                updates = '\n' + indent('\n'.join(updates), '  - ')
            lines.append(f'dependencies: {updates}')

        return '\n'.join(lines)

    @classmethod
    def clean(cls, project: ProjectHandle, db: AnalysisDatabase) -> 'ProjectState':
        about = db.about(project)
        manifest = Manifest.open()
        publish = about.is_published or \
                  manifest.force_publish(project.repo)
        return cls(
            project=project,
            from_version=about.version,
            to_version=about.version,
            version_span=about.version_span,
            language=db.language(project),
            publish=publish,
        )

    def checksum(self, hasher):
        hasher(self.project)
        hasher(self.from_version)
        hasher(self.to_version)
        hasher(self.language)

    def to_raw(self) -> Dict:
        d = {
            'project': str(self.project),
            'language': str(self.language),
            'stage': str(self.stage),
            'from_version': str(self.from_version),
            'to_version': str(self.to_version),
            'version_span': self.version_span.to_raw(),
            'publish': self.publish,
        }

        if self.dependency_updates:
            d['dependency_updates'] = [d.to_raw() for d in self.dependency_updates]

        return d

    @classmethod
    def from_raw(cls, o: Dict) -> 'ProjectState':
        return cls(
            project=ProjectHandle.parse(o['project']),
            from_version=Version.parse(o['from_version']),
            to_version=Version.parse(o['to_version']),
            version_span=Span.from_raw(o['version_span']),
            language=Language(o['language']),
            publish=o['publish'],
            dependency_updates=[DependencyUpdate.from_raw(d)
                                for d in o.get('dependency_updates', [])],
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


def _previous_version(version: Version) -> Version:
    v = list(version.to_tuple())
    v.reverse()
    for i in range(len(v)):
        if v[i] is None or not isinstance(v[i], int):
            pass
        elif v[i] == 0:
            v[i] = 9999
        else:
            v[i] -= 1
            break
    v.reverse()
    return Version(*v)
