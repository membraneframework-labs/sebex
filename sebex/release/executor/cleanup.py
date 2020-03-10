from dataclasses import dataclass
from typing import ClassVar

from sebex.release.executor.types import Task, Action
from sebex.release.state import ReleaseStage


@dataclass
class Cleanup(Task):
    stage: ClassVar[ReleaseStage] = ReleaseStage.DONE

    def run(self) -> Action:
        raise NotImplementedError
