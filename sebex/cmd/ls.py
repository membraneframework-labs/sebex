import click

from sebex.config import current_repository_handles, current_project_handles


@click.command()
@click.option('--projects/--repos', help='List projects or repositories.')
def ls(projects):
    """List repositories in current profile."""

    if projects:
        for project in current_project_handles():
            print(project)
    else:
        for repo in current_repository_handles():
            print(repo)
