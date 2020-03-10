from dataclasses import dataclass

from sebex.release.executor.types import Task, Action
from sebex.release.state import ReleaseStage, ReleaseState


@dataclass
class OpenPullRequest(Task):
    @classmethod
    def stage(cls) -> ReleaseStage:
        return ReleaseStage.PULL_REQUEST_OPENED

    def run(self, release: ReleaseState) -> Action:
        raise NotImplementedError
