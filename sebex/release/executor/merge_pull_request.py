from dataclasses import dataclass
from typing import ClassVar

from sebex.release.executor.types import Task, Action
from sebex.release.state import ReleaseStage, ReleaseState


@dataclass
class MergePullRequest(Task):
    stage: ClassVar[ReleaseStage] = ReleaseStage.PULL_REQUEST_MERGED

    def run(self, release: ReleaseState) -> Action:
        raise NotImplementedError
