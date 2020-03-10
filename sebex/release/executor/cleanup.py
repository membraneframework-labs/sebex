from dataclasses import dataclass
from typing import ClassVar

from sebex.release.executor.types import Task, Action
from sebex.release.state import ReleaseStage, ReleaseState


@dataclass
class Cleanup(Task):
    stage: ClassVar[ReleaseStage] = ReleaseStage.DONE

    def run(self, release: ReleaseState) -> Action:
        raise NotImplementedError
