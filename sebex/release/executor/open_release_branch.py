from dataclasses import dataclass
from typing import ClassVar

from sebex.release.executor.types import Task, Action
from sebex.release.state import ReleaseStage


@dataclass
class OpenReleaseBranch(Task):
    stage: ClassVar[ReleaseStage] = ReleaseStage.BRANCH_OPENED

    def run(self) -> Action:
        raise NotImplementedError
