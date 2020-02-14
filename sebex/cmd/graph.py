import click

from sebex.analysis import AnalysisDatabase, DependencyGraph
from sebex.config import current_project_handles


@click.command()
@click.option('--view', is_flag=True, help='Preview the graph using GraphViz.')
def graph(view):
    """Collect and analyze repository dependency graph."""

    database = AnalysisDatabase.collect(current_project_handles())
    dep_graph = DependencyGraph.build(database)
    dot = dep_graph.graphviz(database)
    if view:
        dot.view(cleanup=True)
    else:
        print(dot.source)
