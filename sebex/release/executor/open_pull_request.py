from dataclasses import dataclass
from typing import ClassVar

from sebex.release.executor.types import Task, Action
from sebex.release.state import ReleaseStage, ReleaseState


@dataclass
class OpenPullRequest(Task):
    stage: ClassVar[ReleaseStage] = ReleaseStage.PULL_REQUEST_OPENED

    def run(self, release: ReleaseState) -> Action:
        raise NotImplementedError
