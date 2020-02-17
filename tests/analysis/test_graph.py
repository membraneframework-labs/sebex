import pytest

from sebex.analysis import Language, Version, VersionSpec, VersionRequirement, DependentsGraph, \
    AnalysisEntry, Dependency
from sebex.config import ProjectHandle
from sebex.edit import Span
from .mock_database import MockAnalysisDatabase

SPAN = Span(0, 0, 0, 5)


def test_builds_empty_database():
    db = MockAnalysisDatabase.mock({})
    graph = DependentsGraph.build(db)
    assert len(graph) == 0


def test_builds_simple():
    db = MockAnalysisDatabase.mock({
        ProjectHandle.parse('a'): (Language.ELIXIR, AnalysisEntry(
            package='a',
            version=Version(1, 0, 0),
            version_span=SPAN,
            dependencies=[
                Dependency(
                    name='b',
                    defined_in='a',
                    version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                    version_spec_span=SPAN
                ),
                Dependency(
                    name='c',
                    defined_in='a',
                    version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                    version_spec_span=SPAN
                )
            ]
        )),
        ProjectHandle.parse('b'): (Language.ELIXIR, AnalysisEntry(
            package='b',
            version=Version(1, 0, 0),
            version_span=SPAN,
            dependencies=[
                Dependency(
                    name='c',
                    defined_in='b',
                    version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                    version_spec_span=SPAN
                )
            ]
        )),
        ProjectHandle.parse('c'): (Language.ELIXIR, AnalysisEntry(
            package='c',
            version=Version(1, 0, 0),
            version_span=SPAN,
        ))
    })

    graph = DependentsGraph.build(db)

    assert len(graph) == 3
    assert list(graph._graph['a'].keys()) == ['b', 'c']
    assert list(graph._graph['b'].keys()) == ['c']
    assert list(graph._graph['c'].keys()) == []


def test_build_detects_cycles():
    db = MockAnalysisDatabase.mock({
        ProjectHandle.parse('a'): (Language.ELIXIR, AnalysisEntry(
            package='a',
            version=Version(1, 0, 0),
            version_span=SPAN,
            dependencies=[
                Dependency(
                    name='b',
                    defined_in='a',
                    version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                    version_spec_span=SPAN
                )
            ]
        )),
        ProjectHandle.parse('b'): (Language.ELIXIR, AnalysisEntry(
            package='b',
            version=Version(1, 0, 0),
            version_span=SPAN,
            dependencies=[
                Dependency(
                    name='c',
                    defined_in='b',
                    version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                    version_spec_span=SPAN
                )
            ]
        )),
        ProjectHandle.parse('c'): (Language.ELIXIR, AnalysisEntry(
            package='c',
            version=Version(1, 0, 0),
            version_span=SPAN,
            dependencies=[
                Dependency(
                    name='a',
                    defined_in='c',
                    version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                    version_spec_span=SPAN
                )
            ]
        ))
    })

    with pytest.raises(ValueError, match='a->b->c->a'):
        DependentsGraph.build(db)


def test_dependents_on():
    db = MockAnalysisDatabase.mock({
        ProjectHandle.parse('a'): (Language.ELIXIR, AnalysisEntry(
            package='a',
            version=Version(1, 0, 0),
            version_span=SPAN,
            dependencies=[
                Dependency(
                    name='b',
                    defined_in='a',
                    version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                    version_spec_span=SPAN
                ),
                Dependency(
                    name='c',
                    defined_in='a',
                    version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                    version_spec_span=SPAN
                )
            ]
        )),
        ProjectHandle.parse('b'): (Language.ELIXIR, AnalysisEntry(
            package='b',
            version=Version(1, 0, 0),
            version_span=SPAN,
            dependencies=[
                Dependency(
                    name='c',
                    defined_in='b',
                    version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                    version_spec_span=SPAN
                ),
                Dependency(
                    name='d',
                    defined_in='b',
                    version_spec=VersionSpec(VersionRequirement.parse('1.0')),
                    version_spec_span=SPAN
                )
            ]
        )),
        ProjectHandle.parse('c'): (Language.ELIXIR, AnalysisEntry(
            package='c',
            version=Version(1, 0, 0),
            version_span=SPAN,
        )),
        ProjectHandle.parse('d'): (Language.ELIXIR, AnalysisEntry(
            package='d',
            version=Version(1, 0, 0),
            version_span=SPAN,
        )),
        ProjectHandle.parse('e:unused'): (Language.ELIXIR, AnalysisEntry(
            package='e',
            version=Version(1, 0, 0),
            version_span=SPAN,
        ))
    })

    graph = DependentsGraph.build(db)

    assert graph.dependents_of('a') == {'b', 'c'}
    assert graph.dependents_of('a', recursive=True) == {'b', 'c', 'd'}
    assert graph.dependents_of('e', recursive=True) == set()

    assert graph.dependents_of_detailed('a') == {
        'b': {Dependency(
            name='b',
            defined_in='a',
            version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
            version_spec_span=SPAN
        )},
        'c': {Dependency(
            name='c',
            defined_in='a',
            version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
            version_spec_span=SPAN
        )}
    }

    assert graph.dependents_of_detailed('a', recursive=True) == {
        'b': {Dependency(
            name='b',
            defined_in='a',
            version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
            version_spec_span=SPAN
        )},
        'c': {
            Dependency(
                name='c',
                defined_in='a',
                version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                version_spec_span=SPAN
            ),
            Dependency(
                name='c',
                defined_in='b',
                version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                version_spec_span=SPAN
            )
        },
        'd': {Dependency(
            name='d',
            defined_in='b',
            version_spec=VersionSpec(VersionRequirement.parse('1.0')),
            version_spec_span=SPAN
        )}
    }
