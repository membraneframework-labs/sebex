from dataclasses import dataclass

from git import Head, GitCommandError

from sebex.config.manifest import Manifest
from sebex.log import operation
from sebex.release.executor.types import Task, Action
from sebex.release.git import release_branch_name
from sebex.release.state import ReleaseStage, ReleaseState


@dataclass
class CloseReleaseBranch(Task):
    @classmethod
    def stage(cls) -> ReleaseStage:
        return ReleaseStage.BRANCH_CLOSED

    def run(self, release: ReleaseState) -> Action:
        git = self.project.project.repo.git
        manifest = Manifest.open().get_repository_by_name(self.project.project.repo)
        branch_name = release_branch_name(self.project)

        with operation(f'Checking out & pulling {manifest.default_branch}'):
            git.git.checkout(manifest.default_branch)
            git.remote().fetch(refspec='refs/heads/*:refs/remotes/origin/*')
            git.git.pull()

        with operation('Deleting remote release branch') as reporter:
            try:
                git.git.push(git.remote().name, '--delete', branch_name)
            except GitCommandError as e:
                if 'remote ref does not exist' in e.stderr:
                    reporter(Action.SKIP.report())
                else:
                    raise

        with operation('Deleting local release branch') as reporter:
            if next((h for h in git.heads if h.name == branch_name), None) is not None:
                Head.delete(git, branch_name)
            else:
                reporter(Action.SKIP.report())

        return Action.PROCEED
