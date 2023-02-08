from dataclasses import dataclass

from github import Repository as GithubRepository
from github.PullRequest import PullRequest

from sebex.config.manifest import Manifest
from sebex.release.executor.types import Task, Action
from sebex.release.git import release_tag_name
from sebex.release.state import ReleaseStage, ReleaseState


@dataclass
class CreateGHRelease(Task):
    @classmethod
    def stage(cls) -> ReleaseStage:
        return ReleaseStage.CREATE_GH_RELEASE

    def run(self, release: ReleaseState) -> Action:
        tag = release_tag_name(self.project)
        vsc = self.project.project.repo.vcs

        # TODO after updating PyGithub lib we should handle creating automatic
        # release notes generation (just sending another bool in POST)
        vsc.create_github_release(tag=tag, message=tag)

        return Action.PROCEED
