from collections import defaultdict
from typing import Dict, Optional, Callable

from sebex.analysis.database import _Projects, AnalysisDatabase
from sebex.analysis.model import Dependency, Language, AnalysisEntry
from sebex.analysis.version import Version, VersionSpec
from sebex.config.manifest import ProjectHandle
from sebex.edit.span import Span


class MockAnalysisDatabase(AnalysisDatabase):
    @classmethod
    def mock(cls, projects: _Projects) -> 'MockAnalysisDatabase':
        return cls._analyze(projects)


def _prepare_versions(versions: Optional[Dict[str, str]] = None) -> Dict[str, Version]:
    if versions is None:
        versions = {}

    return defaultdict(lambda: Version(1, 0, 0),
                       {p: Version.parse(v) for p, v in versions.items()})


def _default_spec(_package: str, depends_on: str, versions: Dict[str, Version]) -> VersionSpec:
    return VersionSpec.targeting(versions[depends_on])


VersionSpecProvider = Callable[[str, str, Dict[str, Version]], VersionSpec]


def _dep(name: str, defined_in: str,
         versions: Dict[str, Version],
         specs: VersionSpecProvider) -> Dependency:
    return Dependency(
        name=name,
        defined_in=defined_in,
        version_spec=specs(defined_in, name, versions),
        version_spec_span=Span.ZERO,
    )


def triangle_db(versions: Dict[str, str] = None,
                specs: VersionSpecProvider = _default_spec) -> AnalysisDatabase:
    versions = _prepare_versions(versions)
    return MockAnalysisDatabase.mock({
        ProjectHandle.parse('a'): (Language.ELIXIR, AnalysisEntry(
            package='a',
            version=versions['a'],
            version_span=Span.ZERO,
            dependencies=[
                _dep('b', 'a', versions, specs),
                _dep('c', 'a', versions, specs)
            ]
        )),
        ProjectHandle.parse('b'): (Language.ELIXIR, AnalysisEntry(
            package='b',
            version=versions['b'],
            version_span=Span.ZERO,
            dependencies=[
                _dep('c', 'b', versions, specs)
            ]
        )),
        ProjectHandle.parse('c'): (Language.ELIXIR, AnalysisEntry(
            package='c',
            version=versions['c'],
            version_span=Span.ZERO,
        ))
    })


def stupid_db(versions: Dict[str, str] = None,
              specs: VersionSpecProvider = _default_spec) -> AnalysisDatabase:
    versions = _prepare_versions(versions)
    return MockAnalysisDatabase.mock({
        ProjectHandle.parse('a'): (Language.ELIXIR, AnalysisEntry(
            package='a',
            version=versions['a'],
            version_span=Span.ZERO,
        )),
        ProjectHandle.parse('b'): (Language.ELIXIR, AnalysisEntry(
            package='b',
            version=versions['b'],
            version_span=Span.ZERO,
            dependencies=[
                _dep('a', 'b', versions, specs),
                _dep('f', 'b', versions, specs)
            ]
        )),
        ProjectHandle.parse('c'): (Language.ELIXIR, AnalysisEntry(
            package='c',
            version=versions['c'],
            version_span=Span.ZERO,
            dependencies=[
                _dep('a', 'c', versions, specs),
                _dep('b', 'c', versions, specs)
            ]
        )),
        ProjectHandle.parse('d'): (Language.ELIXIR, AnalysisEntry(
            package='d',
            version=versions['d'],
            version_span=Span.ZERO,
            dependencies=[
                _dep('b', 'd', versions, specs)
            ]
        )),
        ProjectHandle.parse('e:unused'): (Language.ELIXIR, AnalysisEntry(
            package='e',
            version=versions['e:unused'],
            version_span=Span.ZERO,
        )),
        ProjectHandle.parse('f'): (Language.ELIXIR, AnalysisEntry(
            package='f',
            version=versions['f'],
            version_span=Span.ZERO,
            dependencies=[
                _dep('a', 'f', versions, specs),
            ],
        )),
        ProjectHandle.parse('g'): (Language.ELIXIR, AnalysisEntry(
            package='g',
            version=versions['g'],
            version_span=Span.ZERO,
            dependencies=[
                _dep('f', 'g', versions, specs),
            ],
        )),
    })


def chain_db(height: int = 2, width: int = 1, versions: Dict[str, str] = None,
             specs: VersionSpecProvider = _default_spec) -> AnalysisDatabase:
    def pkg_name(h: int, w: int) -> str:
        # Hack to always point to a0 package, this removes the need to make conditions on this
        if h == 0:
            w = 0

        ys = chr(ord('a') + h)
        return f'{ys}{w}'

    versions = _prepare_versions(versions)

    projects = {
        ProjectHandle.parse(pkg_name(0, 0)): (Language.ELIXIR, AnalysisEntry(
            package=pkg_name(0, 0),
            version=versions[pkg_name(0, 0)],
            version_span=Span.ZERO,
        )),
    }

    for y in range(1, height):
        for x in range(width):
            projects[ProjectHandle.parse(pkg_name(y, x))] = (Language.ELIXIR, AnalysisEntry(
                package=pkg_name(y, x),
                version=versions[pkg_name(y, x)],
                version_span=Span.ZERO,
                dependencies=[
                    _dep(pkg_name(y - 1, x), pkg_name(y, x), versions, specs)
                ]
            ))

    return MockAnalysisDatabase.mock(projects)
