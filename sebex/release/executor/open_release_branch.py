from dataclasses import dataclass

from sebex.language import language_support_for
from sebex.log import operation
from sebex.release.executor.types import Task, Action
from sebex.release.git import release_branch_name
from sebex.release.state import ReleaseStage, ReleaseState


@dataclass
class OpenReleaseBranch(Task):
    @classmethod
    def stage(cls) -> ReleaseStage:
        return ReleaseStage.BRANCH_OPENED

    def run(self, release: ReleaseState) -> Action:
        branch_name = release_branch_name(self.project)

        self.project.project.repo.vcs.checkout(branch_name, delete_existing=True)

        with operation('Modifying project files'):
            language_support_for(self.project.language).write_release(
                self.project.project,
                self.project.to_version,
                self.project.version_span,
                self.project.dependency_updates,
            )

        return Action.PROCEED
