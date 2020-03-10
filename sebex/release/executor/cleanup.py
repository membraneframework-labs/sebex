from dataclasses import dataclass

from sebex.release.executor.types import Task, Action
from sebex.release.state import ReleaseStage, ReleaseState


@dataclass
class Cleanup(Task):
    @classmethod
    def stage(cls) -> ReleaseStage:
        return ReleaseStage.DONE

    def run(self, release: ReleaseState) -> Action:
        raise NotImplementedError
