import click

from sebex.analysis import Version, analyze
from sebex.cli import PROJECT, VERSION, confirm
from sebex.config import ProjectHandle
from sebex.log import success, log, fatal, operation, warn
from sebex.release import ReleaseState, executor


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

    if ReleaseState.exists():
        rel = ReleaseState.open()
        log(rel.describe())
    else:
        success('There is no release pending at this moment, feel free to start one.')


@release.command()
@click.option('--project', type=PROJECT, required=True, prompt=True)
@click.option('--version', type=VERSION, required=True, prompt=True)
@click.option('--dry', is_flag=True,
              help='Print what would be done, but do not persist the generated plan.')
def plan(project: ProjectHandle, version: Version, dry: bool):
    """
    Prepare release plan for managed package.
    """

    if not dry:
        if ReleaseState.exists():
            rel = ReleaseState.open()
            fatal(f'Release "{rel.codename()}" is already running.',
                  'Please finish it before creating new one.')

    database, graph = analyze()
    rel = ReleaseState.plan(project, version, database, graph)

    log()
    log(rel.describe())

    if not dry:
        if confirm('Save this release?'):
            with operation(f'Saving release "{rel.codename()}"'):
                rel.save()


@release.command()
@click.option('--dry', is_flag=True,
              help='Print what would be done, but do not perform any changes.')
def proceed(dry: bool):
    """
    Execute saved release plan until next breakpoint or new phase.
    """

    if not ReleaseState.exists():
        fatal('There is no release pending at this moment. Please create one beforehand.')

    rel = ReleaseState.open()
    if dry:
        for task in executor.plan(rel):
            log(f'{task.project.project}: {task.human_name}')
    else:
        with operation('Proceeding release'):
            with rel.transaction():
                action = executor.proceed(rel)

        if action == executor.Action.FINISH:
            if rel.is_done():
                success('Release finished successfully!')

                with operation('Removing release state file'):
                    rel.delete()
            else:
                success(f'The phase "{rel.current_phase().codename()}" has finished successfully!')
                warn('To proceed, rerun this command.')
        elif action == executor.Action.BREAKPOINT:
            warn('A breakpoint has been reached!')
            warn('Do necessary manual actions and go back here by rerunning this command.')
