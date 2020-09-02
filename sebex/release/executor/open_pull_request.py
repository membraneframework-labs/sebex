from dataclasses import dataclass

from sebex.analysis.version import Version
from sebex.config.manifest import ProjectHandle
from sebex.release.executor.types import Task, Action
from sebex.release.git import release_branch_name, pull_request_title
from sebex.release.state import ReleaseStage, ReleaseState


@dataclass
class OpenPullRequest(Task):
    @classmethod
    def stage(cls) -> ReleaseStage:
        return ReleaseStage.PULL_REQUEST_OPENED

    def run(self, release: ReleaseState) -> Action:
        branch_name = release_branch_name(self.project)
        opened = self.project.project.repo.vcs.open_pull_request(
            title=pull_request_title(self.project),
            body=self._pull_request_body(release),
            branch=branch_name,
        )

        if opened:
            return Action.PROCEED
        else:
            return Action.SKIP

    def _pull_request_body(self, release: ReleaseState) -> str:
        def row(p: ProjectHandle, v: Version):
            return f'| {p} | `{v}` |'

        sources = '\n'.join(row(p, v) for p, v in release.sources.items())

        return f'''\
### Release "{release.codename()}"

| Project | New Version |
|---|---|
{sources}
'''
