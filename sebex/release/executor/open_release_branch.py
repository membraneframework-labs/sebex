from dataclasses import dataclass

from git import Head

from sebex.language import language_support_for
from sebex.log import fatal, warn, operation
from sebex.release.executor.types import Task, Action
from sebex.release.git import release_branch_name
from sebex.release.state import ReleaseStage, ReleaseState


@dataclass
class OpenReleaseBranch(Task):
    @classmethod
    def stage(cls) -> ReleaseStage:
        return ReleaseStage.BRANCH_OPENED

    def run(self, release: ReleaseState) -> Action:
        git = self.project.project.repo.git
        branch_name = release_branch_name(self.project)

        with operation(f'Checking out branch {branch_name}'):
            # Clean existing release branch if it exists
            if branch_name in (h.name for h in git.heads):
                head: Head = next(h for h in git.heads if h.name == branch_name)
                if head.tracking_branch() is not None:
                    fatal(f'Branch {branch_name} is already created and',
                          f'it tracks a remote branch {head.tracking_branch()}.',
                          'Remove both branches before releasing.')
                else:
                    if git.active_branch.name == branch_name:
                        warn('Checking out master before creating release branch')
                        git.git.checkout('master')

                    warn('Deleting existing branch', branch_name)
                    Head.delete(git, branch_name, force=True)

            # Verify that we are on a release-able branch
            if git.is_dirty():
                fatal(f'The branch {git.active_branch} has uncommitted changes.',
                      'Please commit or purge them before running release.')

            git.git.checkout('-b', branch_name)

        with operation('Modifying project files'):
            language_support_for(self.project.language).write_release(
                self.project.project,
                self.project.to_version,
                self.project.version_span,
                self.project.dependency_updates,
            )

        return Action.PROCEED
