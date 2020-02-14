import click

from sebex.analysis import analyze


@click.command()
@click.option('--view', is_flag=True, help='Preview the graph using GraphViz.')
def graph(view):
    """Collect and analyze repository dependency graph."""

    with analyze() as (database, dep_graph):
        dot = dep_graph.graphviz(database)
        if view:
            dot.view(cleanup=True)
        else:
            print(dot.source)
