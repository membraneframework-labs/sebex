from pathlib import Path
from typing import List, Optional

import click
from github import Repository as GithubRepository
from github.PullRequest import PullRequest

from sebex.config.manifest import RepositoryHandle, RepositoryManifest
from sebex.log import log
from sebex.release.state import ProjectState


def release_branch_name(project: ProjectState) -> str:
    return f'release/v{project.to_version}'


def commit(repo: RepositoryHandle, base_message: str, files: List[Path]):
    log('Commit:', click.style(base_message, fg='magenta'))
    repo.git.git.add('--', [p.relative_to(repo.location) for p in files])
    repo.git.git.commit('-m', base_message)


def pull_request_title(project: ProjectState) -> str:
    return f'Release {project.project} v{project.to_version}'


def find_release_pull_request(
    project: ProjectState,
    manifest: RepositoryManifest,
    repo: GithubRepository,
    **filters
) -> Optional[PullRequest]:
    pulls = repo.get_pulls(
        base=manifest.default_branch,
        head=f'{repo.owner.login}:{release_branch_name(project)}',
        **{'state': 'open', 'sort': 'created', 'direction': 'desc', **filters},
    )
    return next(iter(pulls), None)
