import petname
import pytest

from sebex.analysis import DependentsGraph, AnalysisDatabase, Version
from sebex.config import ProjectHandle
from sebex.release import ReleaseState, PhaseState, ProjectReleaseState


@pytest.fixture
def mock_codename(monkeypatch):
    monkeypatch.setattr(petname, 'generate', lambda _, sep: f'code{sep}name')


def test_new_no_release(mock_codename, stupid_db: AnalysisDatabase):
    graph = DependentsGraph.build(stupid_db)
    project = ProjectHandle.parse('a')
    rel = ReleaseState.new(
        project=project,
        to_version=stupid_db.about(project).version,
        db=stupid_db,
        graph=graph
    )
    assert rel == ReleaseState([])


def test_release_stable_patch_without_deps(mock_codename, stupid_db: AnalysisDatabase):
    graph = DependentsGraph.build(stupid_db)
    project = ProjectHandle.parse('e:unused')
    rel = ReleaseState.new(
        project=project,
        to_version=Version.parse('1.0.1'),
        db=stupid_db,
        graph=graph
    )
    assert rel == ReleaseState([
        PhaseState([
            ProjectReleaseState(
                project=project,
                from_version=Version.parse('1.0.0'),
                to_version=Version.parse('1.0.1'),
            )
        ])
    ])


def test_release_stable_minor_without_deps(mock_codename, stupid_db: AnalysisDatabase):
    graph = DependentsGraph.build(stupid_db)
    project = ProjectHandle.parse('e:unused')
    rel = ReleaseState.new(
        project=project,
        to_version=Version.parse('1.1.0'),
        db=stupid_db,
        graph=graph
    )
    assert rel == ReleaseState([
        PhaseState([
            ProjectReleaseState(
                project=project,
                from_version=Version.parse('1.0.0'),
                to_version=Version.parse('1.1.0'),
            )
        ])
    ])


def test_release_stable_major_without_deps(mock_codename, stupid_db: AnalysisDatabase):
    graph = DependentsGraph.build(stupid_db)
    project = ProjectHandle.parse('e:unused')
    rel = ReleaseState.new(
        project=project,
        to_version=Version.parse('2.0.0'),
        db=stupid_db,
        graph=graph
    )
    assert rel == ReleaseState([
        PhaseState([
            ProjectReleaseState(
                project=project,
                from_version=Version.parse('1.0.0'),
                to_version=Version.parse('2.0.0'),
            )
        ])
    ])

# TODO: Test triangle and simple
