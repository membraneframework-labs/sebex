import click

from sebex.analysis.state import analyze


@click.command()
@click.option('--view', is_flag=True, help='Preview the graph using GraphViz.')
def graph(view):
    """Collect and analyze repository dependency graph."""

    database, dep_graph = analyze()
    dot = dep_graph.graphviz(database)
    if view:
        dot.view(cleanup=True)
    else:
        print(dot.source)
