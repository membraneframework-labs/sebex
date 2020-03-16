from dataclasses import dataclass

from git import GitCommandError
from textwrap import dedent

from sebex.cli import confirm
from sebex.config.manifest import Manifest
from sebex.log import operation, log
from sebex.release.executor.types import Task, Action
from sebex.release.git import release_branch_name, find_release_pull_request, pull_request_title
from sebex.release.state import ReleaseStage, ReleaseState, ProjectState


@dataclass
class OpenPullRequest(Task):
    @classmethod
    def stage(cls) -> ReleaseStage:
        return ReleaseStage.PULL_REQUEST_OPENED

    def run(self, release: ReleaseState) -> Action:
        git = self.project.project.repo.git
        github = Manifest.open().get_repository_by_name(self.project.project.repo).github
        branch_name = release_branch_name(self.project)

        with operation(f'Pushing branch {branch_name} to remote repository'):
            try:
                git.git.push('-u', 'origin', branch_name)
            except GitCommandError as e:
                if '[rejected]' in e.stderr and confirm('Push was rejected, try to force push?'):
                    git.git.push('-f', '-u', 'origin', branch_name)
                else:
                    raise

        pr = find_release_pull_request(self.project, github)
        if pr is not None:
            log('Pull request already opened:', pr.html_url)
            return Action.SKIP

        pr = github.create_pull(
            title=pull_request_title(self.project),
            head=branch_name, base=github.default_branch,
            body=self._pull_request_body(release),
        )

        log('Pull request opened:', pr.html_url)
        return Action.PROCEED

    def _pull_request_body(self, release: ReleaseState) -> str:
        def row(p: ProjectState):
            return f'| {p.project} | `{p.from_version}` | `{p.to_version}` |'

        sources = '\n'.join(row(release.get_project(p)) for p in release.sources.keys())

        return dedent(f'''\
        ### Release "{release.codename()}"

        | Project | From | To |
        |---|---|---|
        {sources}

        <sup>proudly automated with \
        <a href="https://github.com/membraneframework/sebex">Sebex</a></sup>
        ''')
