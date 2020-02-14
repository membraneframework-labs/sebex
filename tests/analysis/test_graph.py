import pytest

from sebex.analysis import Language, Version, VersionSpec, VersionRequirement, DependencyGraph
from sebex.analysis.analyzer import AnalysisEntry, Dependency
from sebex.config import ProjectHandle
from sebex.edit import Span
from .mock_database import MockAnalysisDatabase


def test_build_detects_cycles():
    db = MockAnalysisDatabase.mock({
        ProjectHandle.root('a'): (Language.ELIXIR, AnalysisEntry(
            package='a',
            version=Version(1, 0, 0),
            version_span=Span(0, 0, 0, 5),
            dependencies=[
                Dependency(
                    name='b',
                    version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                    version_spec_span=Span(0, 0, 0, 5)
                )
            ]
        )),
        ProjectHandle.root('b'): (Language.ELIXIR, AnalysisEntry(
            package='b',
            version=Version(1, 0, 0),
            version_span=Span(0, 0, 0, 5),
            dependencies=[
                Dependency(
                    name='c',
                    version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                    version_spec_span=Span(0, 0, 0, 5)
                )
            ]
        )),
        ProjectHandle.root('c'): (Language.ELIXIR, AnalysisEntry(
            package='c',
            version=Version(1, 0, 0),
            version_span=Span(0, 0, 0, 5),
            dependencies=[
                Dependency(
                    name='a',
                    version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                    version_spec_span=Span(0, 0, 0, 5)
                )
            ]
        ))
    })

    with pytest.raises(ValueError, match='a->b->c->a'):
        DependencyGraph.build(db)
