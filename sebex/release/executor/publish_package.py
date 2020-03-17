from dataclasses import dataclass

from sebex.language import language_support_for
from sebex.release.executor.types import Task, Action
from sebex.release.state import ReleaseStage, ReleaseState


@dataclass
class PublishPackage(Task):
    @classmethod
    def stage(cls) -> ReleaseStage:
        return ReleaseStage.PUBLISHED

    def run(self, release: ReleaseState) -> Action:
        if not self.project.publish:
            return Action.SKIP

        if language_support_for(self.project.language).publish(self.project.project):
            return Action.PROCEED
        else:
            return Action.BREAKPOINT
