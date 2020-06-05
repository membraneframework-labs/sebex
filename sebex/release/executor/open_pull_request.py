from dataclasses import dataclass
from textwrap import dedent

from sebex.release.executor.types import Task, Action
from sebex.release.git import release_branch_name, pull_request_title
from sebex.release.state import ReleaseStage, ReleaseState, ProjectState


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
        def row(p: ProjectState):
            return f'| {p.project} | `{p.from_version}` | `{p.to_version}` |'

        sources = '\n'.join(row(release.get_project(p)) for p in release.sources.keys())

        return dedent(f'''\
        ### Release "{release.codename()}"

        | Project | From | To |
        |---|---|---|
        {sources}
        ''')
