from dataclasses import dataclass

from sebex.release.executor.types import Task, Action
from sebex.release.state import ReleaseStage, ReleaseState


@dataclass
class PublishPackage(Task):
    @classmethod
    def stage(cls) -> ReleaseStage:
        return ReleaseStage.PUBLISHED

    def run(self, release: ReleaseState) -> Action:
        raise NotImplementedError
