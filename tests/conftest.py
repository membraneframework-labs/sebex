import pytest

from analysis.mock_database import MockAnalysisDatabase
from sebex.analysis import Language, AnalysisEntry, Version, Dependency, VersionSpec, \
    VersionRequirement
from sebex.config import ProjectHandle
from sebex.edit import Span


@pytest.fixture
def triangle_db():
    return MockAnalysisDatabase.mock({
        ProjectHandle.parse('a'): (Language.ELIXIR, AnalysisEntry(
            package='a',
            version=Version(1, 0, 0),
            version_span=Span.ZERO,
            dependencies=[
                Dependency(
                    name='b',
                    defined_in='a',
                    version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                    version_spec_span=Span.ZERO
                ),
                Dependency(
                    name='c',
                    defined_in='a',
                    version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                    version_spec_span=Span.ZERO
                )
            ]
        )),
        ProjectHandle.parse('b'): (Language.ELIXIR, AnalysisEntry(
            package='b',
            version=Version(1, 0, 0),
            version_span=Span.ZERO,
            dependencies=[
                Dependency(
                    name='c',
                    defined_in='b',
                    version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                    version_spec_span=Span.ZERO
                )
            ]
        )),
        ProjectHandle.parse('c'): (Language.ELIXIR, AnalysisEntry(
            package='c',
            version=Version(1, 0, 0),
            version_span=Span.ZERO,
        ))
    })


@pytest.fixture
def stupid_db():
    return MockAnalysisDatabase.mock({
        ProjectHandle.parse('a'): (Language.ELIXIR, AnalysisEntry(
            package='a',
            version=Version(1, 0, 0),
            version_span=Span.ZERO,
        )),
        ProjectHandle.parse('b'): (Language.ELIXIR, AnalysisEntry(
            package='b',
            version=Version(1, 1, 0),
            version_span=Span.ZERO,
            dependencies=[
                Dependency(
                    name='a',
                    defined_in='b',
                    version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                    version_spec_span=Span.ZERO
                ),
                Dependency(
                    name='f',
                    defined_in='b',
                    version_spec=VersionSpec(VersionRequirement.parse('~> 1.1')),
                    version_spec_span=Span.ZERO
                )
            ]
        )),
        ProjectHandle.parse('c'): (Language.ELIXIR, AnalysisEntry(
            package='c',
            version=Version(1, 0, 0),
            version_span=Span.ZERO,
            dependencies=[
                Dependency(
                    name='a',
                    defined_in='c',
                    version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                    version_spec_span=Span.ZERO
                ),
                Dependency(
                    name='b',
                    defined_in='c',
                    version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                    version_spec_span=Span.ZERO
                )
            ]
        )),
        ProjectHandle.parse('d'): (Language.ELIXIR, AnalysisEntry(
            package='d',
            version=Version(1, 0, 0),
            version_span=Span.ZERO,
            dependencies=[
                Dependency(
                    name='b',
                    defined_in='d',
                    version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                    version_spec_span=Span.ZERO
                )
            ]
        )),
        ProjectHandle.parse('e:unused'): (Language.ELIXIR, AnalysisEntry(
            package='e',
            version=Version(1, 0, 0),
            version_span=Span.ZERO,
        )),
        ProjectHandle.parse('f'): (Language.ELIXIR, AnalysisEntry(
            package='f',
            version=Version(1, 1, 0),
            version_span=Span.ZERO,
            dependencies=[
                Dependency(
                    name='a',
                    defined_in='f',
                    version_spec=VersionSpec(VersionRequirement.parse('~> 1.1')),
                    version_spec_span=Span.ZERO
                ),
            ],
        )),
        ProjectHandle.parse('g'): (Language.ELIXIR, AnalysisEntry(
            package='g',
            version=Version(1, 0, 0),
            version_span=Span.ZERO,
            dependencies=[
                Dependency(
                    name='f',
                    defined_in='g',
                    version_spec=VersionSpec(VersionRequirement.parse('~> 1.1.1')),
                    version_spec_span=Span.ZERO
                ),
            ],
        )),
    })
