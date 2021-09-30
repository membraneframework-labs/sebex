from sebex.analysis.database import VIRTUAL_NODE
import click

from sebex.analysis.state import analyze
from sebex.analysis.version import Version
from sebex.cli import PROJECT, VERSION, confirm
from sebex.config.manifest import ProjectHandle, Manifest
from sebex.log import success, log, fatal, operation, warn
from sebex.release.executor import Action, plan as execute_plan, proceed as proceed_plan
from sebex.release.state import ReleaseState
from typing import Optional

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

def gather_input() -> dict[Version, ProjectHandle]:
    bumps = {}
    log("hit enter when done", color='yellow')
    while True:
        value = click.prompt("Project", default="", show_default=False)
        if value == "":
            break
        project = valid_project(value)
        if project is None:
            continue
        # TODO at this moment all packages are bumped by one minor version
        # TODO it would be better to specify different release versions for different packages
        # while True:
        #     value = click.prompt("Version")
        #     version = valid_version(value)
        #     if version is not None:
        #         bumps[project] = version
        #         break
        bumps[project] = None # replace this line with commented code above to use version
    return bumps

# def valid_version(value: str) -> Optional[Version]:
#     try:
#         return Version.parse(value)
#     except ValueError:
#         print(f'{value!r} is not a valid version')
#         return None

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
def plan(dry: bool):
    """
    Prepare release plan for managed packages.
    """

    # gather project names of packages to be released
    bumps = gather_input()
    assert len(bumps) > 0

    if not dry:
        if ReleaseState.exists():
            rel = ReleaseState.open()
            fatal(f'Release "{rel.codename()}" is already running.',
                  'Please finish it before creating new one.')

    database, graph = analyze(bumps)
    # creating the v_project happens under `analyze` in `AnalysisDatabase._add_virtual_root`
    v_project = database.get_project_by_package(VIRTUAL_NODE)
    # bump v_project from 0.1.0 -> 0.2.0 thereby bumping all dependent packages
    rel = ReleaseState.plan(v_project, Version(0, 2, 0), database, graph)

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
                success(f'The phase "{rel.current_phase().codename()}" has finished successfully!')
                warn('To proceed, rerun this command.')
        elif action == Action.BREAKPOINT:
            warn('A breakpoint has been reached!')
            warn('Do necessary manual actions and go back here by rerunning this command.')
