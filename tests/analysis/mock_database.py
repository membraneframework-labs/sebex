from collections import defaultdict
from typing import Dict, Optional

from sebex.analysis import AnalysisDatabase
from sebex.analysis import Language, AnalysisEntry, Version, Dependency, VersionSpec
from sebex.analysis.database import _Projects
from sebex.config import ProjectHandle
from sebex.edit import Span


class MockAnalysisDatabase(AnalysisDatabase):
    @classmethod
    def mock(cls, projects: _Projects) -> 'MockAnalysisDatabase':
        return cls._analyze(projects)


def _prepare_versions(versions: Optional[Dict[str, str]] = None) -> Dict[str, Version]:
    if versions is None:
        versions = {}

    return defaultdict(lambda: Version(1, 0, 0),
                       {p: Version.parse(v) for p, v in versions.items()})


def triangle_db(versions: Dict[str, str] = None) -> AnalysisDatabase:
    versions = _prepare_versions(versions)
    return MockAnalysisDatabase.mock({
        ProjectHandle.parse('a'): (Language.ELIXIR, AnalysisEntry(
            package='a',
            version=versions['a'],
            version_span=Span.ZERO,
            dependencies=[
                Dependency(
                    name='b',
                    defined_in='a',
                    version_spec=VersionSpec.targeting(versions['b']),
                    version_spec_span=Span.ZERO
                ),
                Dependency(
                    name='c',
                    defined_in='a',
                    version_spec=VersionSpec.targeting(versions['c']),
                    version_spec_span=Span.ZERO
                )
            ]
        )),
        ProjectHandle.parse('b'): (Language.ELIXIR, AnalysisEntry(
            package='b',
            version=versions['b'],
            version_span=Span.ZERO,
            dependencies=[
                Dependency(
                    name='c',
                    defined_in='b',
                    version_spec=VersionSpec.targeting(versions['c']),
                    version_spec_span=Span.ZERO
                )
            ]
        )),
        ProjectHandle.parse('c'): (Language.ELIXIR, AnalysisEntry(
            package='c',
            version=versions['c'],
            version_span=Span.ZERO,
        ))
    })


def stupid_db(versions: Dict[str, str] = None) -> AnalysisDatabase:
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
                Dependency(
                    name='a',
                    defined_in='b',
                    version_spec=VersionSpec.targeting(versions['a']),
                    version_spec_span=Span.ZERO
                ),
                Dependency(
                    name='f',
                    defined_in='b',
                    version_spec=VersionSpec.targeting(versions['f']),
                    version_spec_span=Span.ZERO
                )
            ]
        )),
        ProjectHandle.parse('c'): (Language.ELIXIR, AnalysisEntry(
            package='c',
            version=versions['c'],
            version_span=Span.ZERO,
            dependencies=[
                Dependency(
                    name='a',
                    defined_in='c',
                    version_spec=VersionSpec.targeting(versions['a']),
                    version_spec_span=Span.ZERO
                ),
                Dependency(
                    name='b',
                    defined_in='c',
                    version_spec=VersionSpec.targeting(versions['b']),
                    version_spec_span=Span.ZERO
                )
            ]
        )),
        ProjectHandle.parse('d'): (Language.ELIXIR, AnalysisEntry(
            package='d',
            version=versions['d'],
            version_span=Span.ZERO,
            dependencies=[
                Dependency(
                    name='b',
                    defined_in='d',
                    version_spec=VersionSpec.targeting(versions['b']),
                    version_spec_span=Span.ZERO
                )
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
                Dependency(
                    name='a',
                    defined_in='f',
                    version_spec=VersionSpec.targeting(versions['a']),
                    version_spec_span=Span.ZERO
                ),
            ],
        )),
        ProjectHandle.parse('g'): (Language.ELIXIR, AnalysisEntry(
            package='g',
            version=versions['g'],
            version_span=Span.ZERO,
            dependencies=[
                Dependency(
                    name='f',
                    defined_in='g',
                    version_spec=VersionSpec.targeting(versions['f']),
                    version_spec_span=Span.ZERO
                ),
            ],
        )),
    })


def chain_db(height: int = 2, width: int = 1, versions: Dict[str, str] = None) -> AnalysisDatabase:
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
                    Dependency(
                        name=pkg_name(y - 1, x),
                        defined_in=pkg_name(y, x),
                        version_spec=VersionSpec.targeting(versions[pkg_name(y - 1, x)]),
                        version_spec_span=Span.ZERO,
                    )
                ]
            ))

    return MockAnalysisDatabase.mock(projects)
