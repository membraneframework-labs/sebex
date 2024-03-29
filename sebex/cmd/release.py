import click

from sebex.analysis.state import analyze
from sebex.analysis.version import Version
from sebex.cli import confirm, SOURCE
from sebex.config.manifest import ProjectHandle, Manifest
from sebex.log import success, log, fatal, operation, warn
from sebex.release.executor import Action, plan as execute_plan, proceed as proceed_plan
from sebex.release.state import ReleaseState
from typing import Optional, Dict, Tuple


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


def gather_input() -> Dict[Version, ProjectHandle]:
    sources = {}
    log("hit enter when done", color='yellow')
    while True:
        value = click.prompt("Project", default="", show_default=False)
        if value == "":
            if len(sources) == 0:
                log("you must provide at least one project", color="red")
                continue
            else:
                break
        project = valid_project(value)
        if project is None:
            continue
        while True:
            value = click.prompt("Version")
            version = valid_version(value)
            if version is not None:
                sources[project] = version
                break
    return sources


def valid_version(value: str) -> Optional[Version]:
    try:
        return Version.parse(value)
    except ValueError:
        print(f'{value!r} is not a valid version')
        return None


def valid_project(value: str) -> Optional[ProjectHandle]:
    try:
        handle = ProjectHandle.parse(value)
    except ValueError:
        print(f'{value!r} is not a valid project name')
    manifest = Manifest.open()
    for repo_manifest in manifest.iter_repositories():
        for project in repo_manifest.project_handles():
            if project == handle:
                return project
    print(f'Unknown project {handle}')
    return None


@release.command()
@click.option('--dry', is_flag=True,
              help='Print what would be done, but do not persist the generated plan.')
@click.option('--source', '-s', multiple=True, type=SOURCE)
def plan(dry: bool, source):
    """
    Prepare release plan for managed packages.
    """

    # gather project names of packages to be released if none were passed via --source option
    sources = {}
    if source == ():
        sources = gather_input()
    else:
        for p, v in source:
            sources[p] = v

    if not dry:
        if ReleaseState.exists():
            rel = ReleaseState.open()
            fatal(f'Release "{rel.codename()}" is already running.',
                  'Please finish it before creating new one.')

    database, graph = analyze()
    rel = ReleaseState.plan(sources, database, graph)

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
        for task in execute_plan(rel):
            log(f'{task.project.project}: {task.human_name}')
    else:
        with operation('Proceeding release'):
            with rel.transaction():
                action = proceed_plan(rel)

        if action == Action.FINISH:
            if rel.is_done():
                success('Release finished successfully!')

                with operation('Removing release state file'):
                    rel.delete()
            else:
                success(
                    f'The phase "{rel.current_phase().codename()}" has finished successfully!')
                warn('To proceed, rerun this command.')
        elif action == Action.BREAKPOINT:
            warn('A breakpoint has been reached!')
            warn('Do necessary manual actions and go back here by rerunning this command.')
