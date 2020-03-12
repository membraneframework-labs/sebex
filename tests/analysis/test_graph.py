import pytest

from sebex.analysis import Language, Version, VersionSpec, VersionRequirement, DependentsGraph, \
    AnalysisEntry, Dependency
from sebex.config import ProjectHandle
from sebex.edit import Span
from .mock_database import MockAnalysisDatabase, triangle_db, stupid_db


def test_builds_empty_database():
    db = MockAnalysisDatabase.mock({})
    graph = DependentsGraph.build(db)
    assert len(graph) == 0


def test_builds_triangle():
    graph = DependentsGraph.build(triangle_db())

    assert len(graph) == 3
    assert set(graph._graph['a'].keys()) == set()
    assert set(graph._graph['b'].keys()) == {'a'}
    assert set(graph._graph['c'].keys()) == {'a', 'b'}


def test_build_detects_cycles():
    db = MockAnalysisDatabase.mock({
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
            dependencies=[
                Dependency(
                    name='a',
                    defined_in='c',
                    version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                    version_spec_span=Span.ZERO
                )
            ]
        ))
    })

    with pytest.raises(ValueError, match='a->b->c->a'):
        DependentsGraph.build(db)


def test_dependents_of():
    graph = DependentsGraph.build(stupid_db())
    assert graph.dependents_of('a') == {
        'b': {
            Dependency(
                name='a',
                defined_in='b',
                version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                version_spec_span=Span.ZERO
            ),
        },
        'c': {
            Dependency(
                name='a',
                defined_in='c',
                version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                version_spec_span=Span.ZERO
            )
        },
        'f': {
            Dependency(
                name='a',
                defined_in='f',
                version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                version_spec_span=Span.ZERO
            )
        },
    }


def test_upgrade_phases():
    graph = DependentsGraph.build(stupid_db())

    assert graph.upgrade_phases('e') == [{'e'}]
    assert graph.upgrade_phases('d') == [{'d'}]
    assert graph.upgrade_phases('c') == [{'c'}]
    assert graph.upgrade_phases('b') == [{'b'}, {'c', 'd'}]
    assert graph.upgrade_phases('f') == [{'f'}, {'b', 'g'}, {'c', 'd'}]
    assert graph.upgrade_phases('a') == [{'a'}, {'f'}, {'b', 'g'}, {'c', 'd'}]
