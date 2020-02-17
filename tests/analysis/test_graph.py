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
    assert set(graph._graph['a'].keys()) == set()
    assert set(graph._graph['b'].keys()) == {'a'}
    assert set(graph._graph['c'].keys()) == {'a', 'b'}


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


STUPID_DB = MockAnalysisDatabase.mock({
    ProjectHandle.parse('a'): (Language.ELIXIR, AnalysisEntry(
        package='a',
        version=Version(1, 0, 0),
        version_span=SPAN,
    )),
    ProjectHandle.parse('b'): (Language.ELIXIR, AnalysisEntry(
        package='b',
        version=Version(1, 1, 0),
        version_span=SPAN,
        dependencies=[
            Dependency(
                name='a',
                defined_in='b',
                version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                version_spec_span=SPAN
            ),
            Dependency(
                name='f',
                defined_in='b',
                version_spec=VersionSpec(VersionRequirement.parse('~> 1.1')),
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
            ),
            Dependency(
                name='b',
                defined_in='c',
                version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                version_spec_span=SPAN
            )
        ]
    )),
    ProjectHandle.parse('d'): (Language.ELIXIR, AnalysisEntry(
        package='d',
        version=Version(1, 0, 0),
        version_span=SPAN,
        dependencies=[
            Dependency(
                name='b',
                defined_in='d',
                version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                version_spec_span=SPAN
            )
        ]
    )),
    ProjectHandle.parse('e:unused'): (Language.ELIXIR, AnalysisEntry(
        package='e',
        version=Version(1, 0, 0),
        version_span=SPAN,
    )),
    ProjectHandle.parse('f'): (Language.ELIXIR, AnalysisEntry(
        package='f',
        version=Version(1, 1, 0),
        version_span=SPAN,
        dependencies=[
            Dependency(
                name='a',
                defined_in='f',
                version_spec=VersionSpec(VersionRequirement.parse('~> 1.1')),
                version_spec_span=SPAN
            ),
        ],
    )),
})


def test_dependents_of():
    graph = DependentsGraph.build(STUPID_DB)
    # print(graph.graphviz(STUPID_DB).view(cleanup=True))

    assert graph.dependents_of('a') == {'b', 'c', 'f'}
    assert graph.dependents_of('a', recursive=True) == {'b', 'c', 'd', 'f'}
    assert graph.dependents_of('e', recursive=True) == set()

    assert graph.dependents_of_detailed('a') == {
        'b': {
            Dependency(
                name='a',
                defined_in='b',
                version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                version_spec_span=SPAN
            ),
        },
        'c': {
            Dependency(
                name='a',
                defined_in='c',
                version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                version_spec_span=SPAN
            )
        },
        'f': {
            Dependency(
                name='a',
                defined_in='f',
                version_spec=VersionSpec(VersionRequirement.parse('~> 1.1')),
                version_spec_span=SPAN
            )
        },
    }

    assert graph.dependents_of_detailed('a', recursive=True) == {
        'b': {
            Dependency(
                name='a',
                defined_in='b',
                version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                version_spec_span=SPAN
            ),
            Dependency(
                name='f',
                defined_in='b',
                version_spec=VersionSpec(VersionRequirement.parse('~> 1.1')),
                version_spec_span=SPAN
            ),
        },
        'c': {
            Dependency(
                name='a',
                defined_in='c',
                version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                version_spec_span=SPAN
            ),
            Dependency(
                name='b',
                defined_in='c',
                version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                version_spec_span=SPAN
            )
        },
        'd': {
            Dependency(
                name='b',
                defined_in='d',
                version_spec=VersionSpec(VersionRequirement.parse('~> 1.0')),
                version_spec_span=SPAN
            )
        },
        'f': {
            Dependency(
                name='a',
                defined_in='f',
                version_spec=VersionSpec(VersionRequirement.parse('~> 1.1')),
                version_spec_span=SPAN
            )
        },
    }


def test_upgrade_phases():
    graph = DependentsGraph.build(STUPID_DB)

    assert graph.upgrade_phases('e') == [{'e'}]
    assert graph.upgrade_phases('d') == [{'d'}]
    assert graph.upgrade_phases('c') == [{'c'}]
    assert graph.upgrade_phases('b') == [{'b'}, {'c', 'd'}]
    assert graph.upgrade_phases('f') == [{'f'}, {'b'}, {'c', 'd'}]
    assert graph.upgrade_phases('a') == [{'a'}, {'f'}, {'b'}, {'c', 'd'}]
