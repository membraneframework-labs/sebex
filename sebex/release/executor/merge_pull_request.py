from dataclasses import dataclass
from typing import ClassVar

from sebex.release.executor.types import Task, Action
from sebex.release.state import ReleaseStage


@dataclass
class MergePullRequest(Task):
    stage: ClassVar[ReleaseStage] = ReleaseStage.PULL_REQUEST_MERGED

    def run(self) -> Action:
        raise NotImplementedError
