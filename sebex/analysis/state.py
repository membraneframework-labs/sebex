from sebex.analysis.version import Version
from sebex.config.manifest import ProjectHandle
from typing import Tuple

from sebex.analysis.database import AnalysisDatabase
from sebex.analysis.graph import DependentsGraph
from sebex.config.profile import current_project_handles


def analyze() -> Tuple[AnalysisDatabase, DependentsGraph]:
    database = AnalysisDatabase.collect(current_project_handles())
    graph = DependentsGraph.build(database)
    return database, graph
