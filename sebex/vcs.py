import re
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import List, Optional

import click
from git import Head, Repo as GitRepo, GitCommandError
from github import Repository as GithubRepository
from github.PullRequest import PullRequest

from sebex.cli import confirm
from sebex.config.manifest import RepositoryHandle, Manifest
from sebex.context import Context
from sebex.log import log, operation, fatal, warn

_GITHUB_SSH_URL = re.compile(r'git@github\.com:(?P<full>(?P<org>[^/]+)/(?P<repo>.+))\.git/?')
_PR_MARKETING = r'''

<sup>proudly automated with <a href="https://github.com/membraneframework/sebex">Sebex</a></sup>
'''

_SKIP = click.style('SKIPPED', fg='yellow')


@dataclass
class Vcs:
    """
    A central facade over Git & GitHub operations on repository.
    """

    repo: RepositoryHandle

    @property
    def location(self) -> Path:
        return self.repo.location

    @cached_property
    def git(self) -> GitRepo:
        return GitRepo(self.location)

    @cached_property
    def github(self) -> GithubRepository:
        manifest = Manifest.open().get_repository_by_name(self.repo)
        m = _GITHUB_SSH_URL.match(manifest.remote_url)
        if m:
            return Context.current().github.get_repo(m['full'], lazy=True)
        else:
            raise ValueError('Repository is not hosted on GitHub')

    @cached_property
    def default_branch(self) -> str:
        manifest = Manifest.open().get_repository_by_name(self.repo)
        return manifest.default_branch

    @property
    def active_branch(self) -> str:
        return self.git.active_branch.name

    @property
    def default_remote(self) -> str:
        return self.git.remote().name

    def is_dirty(self) -> bool:
        return self.git.is_dirty()

    def is_tracked(self, file: Path) -> bool:
        return file.resolve() in ((self.location / line).resolve()
                                  for line in self.git.git.ls_files().split('\n'))

    def is_changed(self, file: Path) -> bool:
        return file.resolve() in ((self.location / item.a_path).resolve()
                                  for item in self.git.index.diff(None))

    def branch_exists(self, branch: str) -> bool:
        return branch in (h.name for h in self.git.heads)

    def fetch(self):
        with operation('Fetching', self.repo):
            self.git.remote().fetch(refspec='refs/heads/*:refs/remotes/origin/*')
            self.git.remote().fetch(refspec='refs/tags/*:refs/tags/*')

    def pull(self):
        with operation('Pulling', self.repo):
            self.git.remote().pull()

    def commit(self, base_message: str, files: List[Path] = None):
        log('Commit:', click.style(base_message, fg='magenta'))

        if files:
            self.git.git.add('--', [p.relative_to(self.location) for p in files])
        else:
            self.git.git.add('.')

        self.git.git.commit('-m', base_message)

    def tag(self, tag: str, message=None):
        self.git.create_tag(tag, message=message)

    def checkout(self, branch: str, ensure_clean: bool = True, delete_existing: bool = False):
        with operation(f'Checking out branch {branch}'):
            # Clean existing (remote) branch if it exists
            if delete_existing and self.branch_exists(branch):
                head: Head = next(h for h in self.git.heads if h.name == branch)
                if head.tracking_branch() is not None:
                    fatal(f'Branch {branch} is already created and',
                          f'it tracks a remote branch {head.tracking_branch()}.',
                          'Remove both branches before making changes.')
                else:
                    if self.active_branch == branch:
                        warn('Checking out', self.default_branch,
                             'before creating branch', branch)
                        self.git.git.checkout(self.default_branch)

                    warn('Deleting existing branch', branch)
                    Head.delete(self.git, branch, force=True)

            # Verify that we are in clean state
            if ensure_clean and self.is_dirty():
                fatal(f'The branch {self.active_branch} has uncommitted changes.',
                      'Please commit or purge them before proceeding with changes.')

            self.git.git.checkout('-b', branch)

    def push(self, branch: str = None, tag: str = None):
        def do_push(*args):
            try:
                self.git.git.push(*args)
            except GitCommandError as e:
                if '[rejected]' in e.stderr and confirm('Push was rejected, try to force push?'):
                    self.git.git.push('-f', *args)
                else:
                    raise

        if branch:
            with operation(f'Pushing branch {branch} to remote repository'):
                do_push('-u', 'origin', branch)

        if tag:
            with operation(f'Pushing tag {tag} to remote repository'):
                do_push('origin', tag)

    def delete_local_branch(self, branch: str):
        with operation(f'Deleting local branch {branch}') as reporter:
            if self.branch_exists(branch):
                Head.delete(self.git, branch)
            else:
                reporter(_SKIP)

    def delete_remote_branch(self, branch: str):
        with operation(f'Deleting remote branch {self.default_remote}/{branch}') as reporter:
            try:
                self.git.git.push(self.default_remote, '--delete', branch)
            except GitCommandError as e:
                if 'remote ref does not exist' in e.stderr:
                    reporter(_SKIP)
                else:
                    raise

    def find_pull_request(self, branch: str, **filters) -> Optional[PullRequest]:
        pulls = self.github.get_pulls(
            base=self.default_branch,
            head=f'{self.github.owner.login}:{branch}',
            **{'state': 'open', 'sort': 'created', 'direction': 'desc', **filters},
        )
        return next(iter(pulls), None)

    def open_pull_request(self, title: str, body: str, branch: str = None, base: str = None,
                          push: bool = True) -> bool:
        if not branch:
            branch = self.active_branch

        if not base:
            base = self.default_branch

        if push:
            self.push(branch=branch)

        pr = self.find_pull_request(branch=branch)
        if pr is not None:
            log('Pull request already opened:', pr.html_url)
            return False

        body = body + _PR_MARKETING
        body = body.strip()

        pr = self.github.create_pull(title=title, head=branch, base=base, body=body)

        log('Pull request opened:', pr.html_url)
        return True
