from dataclasses import dataclass

from git import Head

from sebex.languages import language_support_for
from sebex.log import log, fatal, warn
from sebex.release.executor.types import Task, Action
from sebex.release.executor.util import release_branch_name
from sebex.release.state import ReleaseStage, ReleaseState


@dataclass
class OpenReleaseBranch(Task):
    @classmethod
    def stage(cls) -> ReleaseStage:
        return ReleaseStage.BRANCH_OPENED

    def run(self, release: ReleaseState) -> Action:
        handle = self.project.project
        git = handle.repo.git
        branch_name = release_branch_name(self.project)

        # Clean existing release branch if it exists
        if branch_name in (h.name for h in git.heads):
            head: Head = next(h for h in git.heads if h.name == branch_name)
            if head.tracking_branch() is not None:
                fatal(f'Branch {branch_name} is already created and',
                      f'it tracks a remote branch {head.tracking_branch()}.',
                      'Remove both branches before releasing.')
            else:
                if git.active_branch.name == branch_name:
                    warn('Checking out master')
                    git.git.checkout('master')

                warn('Deleting existing branch', branch_name)
                Head.delete(git, branch_name, force=True)

        # Verify that we are on a release-able branch
        log('Releasing from branch:', git.active_branch)
        if git.is_dirty():
            fatal('This branch has uncommitted changes.',
                  'Please commit or purge them before running release.')

        # Checkout
        log('Checking out branch', branch_name)
        git.git.checkout('-b', branch_name)

        # Perform necessary editions
        language_support = language_support_for(self.project.language)

        raise NotImplementedError
