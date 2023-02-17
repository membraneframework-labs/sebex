from dataclasses import dataclass

from github import Repository as GithubRepository
from github.PullRequest import PullRequest

from sebex.config.manifest import Manifest
from sebex.release.executor.types import Task, Action
from sebex.release.git import release_tag_name
from sebex.release.state import ReleaseStage, ReleaseState


@dataclass
class CreateGithubRelease(Task):
    @classmethod
    def stage(cls) -> ReleaseStage:
        return ReleaseStage.CREATE_GITHUB_RELEASE

    def run(self, release: ReleaseState) -> Action:
        tag = release_tag_name(self.project)
        vcs = self.project.project.repo.vcs

        vcs.create_github_release(tag=tag, message=tag)

        return Action.PROCEED
