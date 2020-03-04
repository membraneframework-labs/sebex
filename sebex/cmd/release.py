import click

from sebex.analysis import Version, analyze
from sebex.cli import PROJECT, VERSION
from sebex.config import ProjectHandle
from sebex.log import success, log, fatal, operation
from sebex.release.state import ReleaseState


@click.group()
def release():
    """
    Prepare and execute release plan for managed package.
    """

    pass


@release.command()
def status():
    """
    Show status of currently pending release (if any).
    """

    success('There is no release pending at this moment, feel free to start one.')


@release.command()
@click.option('--project', type=PROJECT, required=True, prompt=True)
@click.option('--version', type=VERSION, required=True, prompt=True)
@click.option('-n', '--noop', is_flag=True,
              help='Print what would be done, but do not persist the generated plan.')
def plan(project: ProjectHandle, version: Version, noop: bool):
    """
    Prepare release plan for managed package.
    """

    if not noop:
        if ReleaseState.exists():
            rel = ReleaseState.open()
            fatal(f'Release "{rel.codename()}" is already running.',
                  'Please finish it before creating new one.')

    database, graph = analyze()
    rel = ReleaseState.plan(project, version, database, graph)

    log()
    log(rel.describe())

    if not noop:
        with operation(f'Saving release "{rel.codename()}"'):
            rel.save()


@release.command(name='continue')
@click.option('-n', '--noop', is_flag=True,
              help='Print what would be done, but do not execute anything.')
def cont(noop: bool):
    """
    Execute saved release plan until next breakpoint.
    """

    pass
