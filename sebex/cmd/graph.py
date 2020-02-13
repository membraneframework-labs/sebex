import pprint

import click

from sebex.analysis import AnalysisDatabase
from sebex.config import current_project_handles


@click.command()
def graph():
    """Collect and analyze repository dependency graph."""

    database = AnalysisDatabase.collect(current_project_handles())
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(database._data)
