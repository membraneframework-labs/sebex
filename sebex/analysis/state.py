from contextlib import contextmanager
from typing import NamedTuple

from sebex.analysis.database import AnalysisDatabase
from sebex.analysis.graph import DependentsGraph
from sebex.config import current_project_handles


class AnalysisState(NamedTuple):
    database: AnalysisDatabase
    graph: DependentsGraph


@contextmanager
def analyze():
    # Written as context manager as we foresee that it might be worth caching it.

    database = AnalysisDatabase.collect(current_project_handles())
    graph = DependentsGraph.build(database)

    yield AnalysisState(database, graph)
