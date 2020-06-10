from dataclasses import dataclass

from sebex.release.executor.types import Task, Action
from sebex.release.git import release_branch_name, release_tag_name
from sebex.release.state import ReleaseStage, ReleaseState


@dataclass
class CloseReleaseBranch(Task):
    @classmethod
    def stage(cls) -> ReleaseStage:
        return ReleaseStage.BRANCH_CLOSED

    def run(self, release: ReleaseState) -> Action:
        branch = release_branch_name(self.project)
        tag = release_tag_name(self.project)
        vcs = self.project.project.repo.vcs

        vcs.checkout(vcs.default_branch)
        vcs.fetch()
        vcs.pull()

        vcs.delete_remote_branch(branch)
        vcs.delete_local_branch(branch)

        vcs.tag(tag)
        vcs.push(tag=tag)

        return Action.PROCEED
