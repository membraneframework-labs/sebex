import re
from typing import Optional

import click

from sebex.checksum import Checksum
from sebex.config.profile import current_repository_handles
from sebex.log import logcontext, log, error
from sebex.popen import popen


@click.command()
@click.argument('command')
@click.option('--pr/--no-pr', ' /-P', default=True, help='No not try to open pull request.')
@click.option('-t', '--title',
              help='Pull request title, if not specified a codename will be generated.')
@click.option('-b', '--body', default='', show_default=True, help='Pull request body.')
def foreach(command: str, pr: bool, title: Optional[str], body: str):
    """
    Execute a shell command for each repository in current profile and open pull request
    with changes if any.

    Clean state of repository is checked before executing the script. If repository is
    dirty, then operation is aborted. It is recommended to make scripts idempotent.
    """

    title: str = title if title else Checksum.of(command).petname

    branch = title.lower()
    branch = re.sub(r'[^a-z0-9 -_]', '', branch)
    branch = re.sub(r'[-_\s]+', '-', branch)
    branch = branch[:16]
    branch = branch.strip('-')

    for repo in current_repository_handles():
        with logcontext(str(repo)):
            if repo.vcs.is_dirty():
                error('Repository is not in clean state! Ignoring.')
                continue

            base = repo.vcs.active_branch

            popen(command, log_stdout=True, shell=True, cwd=repo.location)

            if pr:
                if not repo.vcs.is_dirty():
                    log('No changes were made.')
                else:
                    repo.vcs.checkout(branch, ensure_clean=False)
                    repo.vcs.commit(title)
                    repo.vcs.open_pull_request(title=title, body=body, branch=branch, base=base)
                    repo.vcs.checkout(base)
