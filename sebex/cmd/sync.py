import click
from git import Repo

from sebex.config.manifest import RepositoryManifest
from sebex.config.profile import current_repositories
from sebex.jobs import for_each
from sebex.log import error, success, operation


@click.command()
@click.option('--clone/--no-clone', default=True, help='Attempt to clone new repositories.')
@click.option('--fetch/--pull', default=False, help='Run fetch only, do not pull any changes.')
def sync(clone, fetch):
    """Sync repositories in current profile."""

    def do_sync(manifest: RepositoryManifest):
        repo = manifest.handle
        if not repo.exists():
            if clone:
                with operation('Cloning', repo):
                    Repo.clone_from(manifest.remote_url, manifest.location)
            else:
                error('Repository is not cloned:', repo)
        else:
            if fetch:
                repo.vcs.pull()
            else:
                repo.vcs.pull()

    repos = list(current_repositories())
    for_each(repos, do_sync, desc='Syncing', item_desc=lambda r: r.handle)
    success('Successfully synced', len(repos), 'repositories.')
