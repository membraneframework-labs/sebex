import click

from sebex.analysis import Version, analyze
from sebex.cli import PROJECT, VERSION
from sebex.config import ProjectHandle
from sebex.release.state import ReleaseState


@click.group()
def release():
    """
    Prepare and execute release plan for managed package.
    """

    pass


@release.command()
@click.option('--project', type=PROJECT, required=True, prompt=True)
@click.option('--version', type=VERSION, required=True, prompt=True)
@click.option('-n', '--noop', is_flag=True,
              help='Print what will be done, but do not execute anything.')
def plan(project: ProjectHandle, version: Version, noop: bool):
    """
    Prepare release plan for managed package.
    """

    database, graph = analyze()
    rel = ReleaseState.plan(project, version, database, graph)
    print('------')
    print(rel)


@release.command(name='continue')
@click.option('-n', '--noop', is_flag=True,
              help='Print what will be done, but do not execute anything.')
def cont(noop: bool):
    """
    Execute saved release plan until next breakpoint.
    """

    pass
