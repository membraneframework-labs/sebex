from pathlib import Path
from typing import Optional

import click

from sebex.config.manifest import Manifest, RepositoryManifest
from sebex.context import Context


@click.command()
@click.option('-o', '--organization',
              help='Name of Github organization to import repositories from.')
def bootstrap(organization: Optional[str]):
    """
    Set up workspace directories and/or load add all repositories from specified Github
    organization.
    """

    Path(Context.current().meta_path).mkdir(parents=True, exist_ok=True)
    with Manifest.open().transaction() as manifest:
        if organization:
            org = Context.current().github.get_organization(organization)
            for gh_repo in sorted(org.get_repos(type='public'), key=lambda r: r.full_name):
                repo = RepositoryManifest.from_github_repository(gh_repo)
                manifest.upsert_repository(repo)
