from pathlib import Path
from typing import List

import click

from sebex.config.manifest import RepositoryHandle
from sebex.log import log
from sebex.release.state import ProjectState


def release_branch_name(project: ProjectState) -> str:
    return f'release/v{project.to_version}'


def commit(repo: RepositoryHandle, base_message: str, files: List[Path]):
    log('Commit:', click.style(base_message, fg='magenta'))
    repo.git.git.add('--', [p.relative_to(repo.location) for p in files])
    repo.git.git.commit('-m', base_message)
