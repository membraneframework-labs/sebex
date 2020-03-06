from analysis.mock_database import chain_db, triangle_db
from sebex.analysis import DependentsGraph, Version
from sebex.checksum import Checksum
from sebex.config import ProjectHandle
from sebex.release import ReleaseState, PhaseState, ProjectReleaseState


def test_petname_deterministic():
    db = chain_db(1)
    assert Checksum.of(db) == Checksum('feccf1c633f39b97d339786c864c9eb079ef4c20')
    assert Checksum.of(db).petname == 'Duly Up Pup'


def test_new_no_release():
    db = chain_db(1)
    graph = DependentsGraph.build(db)
    project = ProjectHandle.parse('a0')
    rel = ReleaseState.plan(
        project=project,
        to_version=db.about(project).version,
        db=db,
        graph=graph
    )
    assert rel == ReleaseState(sources={}, phases=[])


def test_release_stable_patch_without_deps():
    db = chain_db(1)
    graph = DependentsGraph.build(db)
    rel = ReleaseState.plan(
        project=ProjectHandle.parse('a0'),
        to_version=Version.parse('1.0.1'),
        db=db,
        graph=graph
    )
    assert rel == ReleaseState(
        sources={ProjectHandle.parse('a0'): Version.parse('1.0.1')},
        phases=[
            PhaseState([
                ProjectReleaseState(
                    project=ProjectHandle.parse('a0'),
                    from_version=Version.parse('1.0.0'),
                    to_version=Version.parse('1.0.1'),
                )
            ])
        ],
    )


def test_release_stable_minor_without_deps():
    db = chain_db(1)
    graph = DependentsGraph.build(db)
    rel = ReleaseState.plan(
        project=ProjectHandle.parse('a0'),
        to_version=Version.parse('1.1.0'),
        db=db,
        graph=graph
    )
    assert rel == ReleaseState(
        sources={ProjectHandle.parse('a0'): Version.parse('1.1.0')},
        phases=[
            PhaseState([
                ProjectReleaseState(
                    project=ProjectHandle.parse('a0'),
                    from_version=Version.parse('1.0.0'),
                    to_version=Version.parse('1.1.0'),
                )
            ])
        ],
    )


def test_release_stable_major_without_deps():
    db = chain_db(1)
    graph = DependentsGraph.build(db)
    rel = ReleaseState.plan(
        project=ProjectHandle.parse('a0'),
        to_version=Version.parse('2.0.0'),
        db=db,
        graph=graph
    )
    assert rel == ReleaseState(
        sources={ProjectHandle.parse('a0'): Version.parse('2.0.0')},
        phases=[
            PhaseState([
                ProjectReleaseState(
                    project=ProjectHandle.parse('a0'),
                    from_version=Version.parse('1.0.0'),
                    to_version=Version.parse('2.0.0'),
                )
            ])
        ],
    )


def test_release_stable_patch_with_one_level_of_deps():
    db = chain_db()
    graph = DependentsGraph.build(db)
    rel = ReleaseState.plan(
        project=ProjectHandle.parse('a0'),
        to_version=Version.parse('1.0.1'),
        db=db,
        graph=graph
    )
    assert rel == ReleaseState(
        sources={ProjectHandle.parse('a0'): Version.parse('1.0.1')},
        phases=[
            PhaseState([
                ProjectReleaseState(
                    project=ProjectHandle.parse('a0'),
                    from_version=Version.parse('1.0.0'),
                    to_version=Version.parse('1.0.1'),
                )
            ]),
            PhaseState([
                ProjectReleaseState(
                    project=ProjectHandle.parse('b0'),
                    from_version=Version.parse('1.0.0'),
                    to_version=Version.parse('1.0.1'),
                )
            ]),
        ],
    )


def test_release_stable_minor_with_one_level_of_deps():
    db = chain_db()
    graph = DependentsGraph.build(db)
    rel = ReleaseState.plan(
        project=ProjectHandle.parse('a0'),
        to_version=Version.parse('1.1.0'),
        db=db,
        graph=graph
    )
    assert rel == ReleaseState(
        sources={ProjectHandle.parse('a0'): Version.parse('1.1.0')},
        phases=[
            PhaseState([
                ProjectReleaseState(
                    project=ProjectHandle.parse('a0'),
                    from_version=Version.parse('1.0.0'),
                    to_version=Version.parse('1.1.0'),
                )
            ]),
            PhaseState([
                ProjectReleaseState(
                    project=ProjectHandle.parse('b0'),
                    from_version=Version.parse('1.0.0'),
                    to_version=Version.parse('1.0.1'),
                )
            ]),
        ],
    )


def test_release_stable_major_with_one_level_of_deps():
    db = chain_db()
    graph = DependentsGraph.build(db)
    rel = ReleaseState.plan(
        project=ProjectHandle.parse('a0'),
        to_version=Version.parse('2.0.0'),
        db=db,
        graph=graph
    )
    assert rel == ReleaseState(
        sources={ProjectHandle.parse('a0'): Version.parse('2.0.0')},
        phases=[
            PhaseState([
                ProjectReleaseState(
                    project=ProjectHandle.parse('a0'),
                    from_version=Version.parse('1.0.0'),
                    to_version=Version.parse('2.0.0'),
                )
            ]),
            PhaseState([
                ProjectReleaseState(
                    project=ProjectHandle.parse('b0'),
                    from_version=Version.parse('1.0.0'),
                    to_version=Version.parse('1.1.0'),
                )
            ]),
        ],
    )


def test_release_indirect_bump_with_one_level_of_deps():
    db = chain_db()
    graph = DependentsGraph.build(db)
    rel = ReleaseState.plan(
        project=ProjectHandle.parse('a0'),
        to_version=Version.parse('1.2.3'),
        db=db,
        graph=graph
    )
    assert rel == ReleaseState(
        sources={ProjectHandle.parse('a0'): Version.parse('1.2.3')},
        phases=[
            PhaseState([
                ProjectReleaseState(
                    project=ProjectHandle.parse('a0'),
                    from_version=Version.parse('1.0.0'),
                    to_version=Version.parse('1.2.3'),
                )
            ]),
            PhaseState([
                ProjectReleaseState(
                    project=ProjectHandle.parse('b0'),
                    from_version=Version.parse('1.0.0'),
                    to_version=Version.parse('1.0.1'),
                )
            ]),
        ],
    )


def test_release_pre_patch():
    db = chain_db(width=2, versions={'a0': '0.1.0', 'b0': '1.0.0', 'b1': '0.1.0'})
    graph = DependentsGraph.build(db)
    rel = ReleaseState.plan(
        project=ProjectHandle.parse('a0'),
        to_version=Version.parse('0.1.1'),
        db=db,
        graph=graph
    )
    assert rel == ReleaseState(
        sources={ProjectHandle.parse('a0'): Version.parse('0.1.1')},
        phases=[
            PhaseState([
                ProjectReleaseState(
                    project=ProjectHandle.parse('a0'),
                    from_version=Version.parse('0.1.0'),
                    to_version=Version.parse('0.1.1'),
                )
            ]),
            PhaseState([
                ProjectReleaseState(
                    project=ProjectHandle.parse('b0'),
                    from_version=Version.parse('1.0.0'),
                    to_version=Version.parse('1.0.1'),
                ),
                ProjectReleaseState(
                    project=ProjectHandle.parse('b1'),
                    from_version=Version.parse('0.1.0'),
                    to_version=Version.parse('0.1.1'),
                ),
            ]),
        ],
    )


def test_release_pre_minor():
    db = chain_db(width=2, versions={'a0': '0.1.0', 'b0': '1.0.0', 'b1': '0.1.0'})
    graph = DependentsGraph.build(db)
    rel = ReleaseState.plan(
        project=ProjectHandle.parse('a0'),
        to_version=Version.parse('0.2.0'),
        db=db,
        graph=graph
    )
    assert rel == ReleaseState(
        sources={ProjectHandle.parse('a0'): Version.parse('0.2.0')},
        phases=[
            PhaseState([
                ProjectReleaseState(
                    project=ProjectHandle.parse('a0'),
                    from_version=Version.parse('0.1.0'),
                    to_version=Version.parse('0.2.0'),
                )
            ]),
            PhaseState([
                ProjectReleaseState(
                    project=ProjectHandle.parse('b0'),
                    from_version=Version.parse('1.0.0'),
                    to_version=Version.parse('1.1.0'),
                ),
                ProjectReleaseState(
                    project=ProjectHandle.parse('b1'),
                    from_version=Version.parse('0.1.0'),
                    to_version=Version.parse('0.2.0'),
                ),
            ]),
        ],
    )


def test_transitive_dep():
    db = triangle_db()
    graph = DependentsGraph.build(db)
    rel = ReleaseState.plan(
        project=ProjectHandle.parse('c'),
        to_version=Version.parse('2.0.0'),
        db=db,
        graph=graph
    )
    assert rel == ReleaseState(
        sources={ProjectHandle.parse('c'): Version.parse('2.0.0')},
        phases=[
            PhaseState([
                ProjectReleaseState(
                    project=ProjectHandle.parse('c'),
                    from_version=Version.parse('1.0.0'),
                    to_version=Version.parse('2.0.0'),
                ),
            ]),
            PhaseState([
                ProjectReleaseState(
                    project=ProjectHandle.parse('b'),
                    from_version=Version.parse('1.0.0'),
                    to_version=Version.parse('1.1.0'),
                ),
            ]),
            PhaseState([
                ProjectReleaseState(
                    project=ProjectHandle.parse('a'),
                    from_version=Version.parse('1.0.0'),
                    to_version=Version.parse('1.1.0'),
                ),
            ]),
        ],
    )
