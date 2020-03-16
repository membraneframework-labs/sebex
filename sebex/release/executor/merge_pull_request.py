from dataclasses import dataclass

from github import Repository as GithubRepository
from github.PullRequest import PullRequest

from sebex.cli import confirm
from sebex.config.manifest import Manifest
from sebex.log import success, error, log
from sebex.release.executor.types import Task, Action
from sebex.release.git import find_release_pull_request
from sebex.release.state import ReleaseStage, ReleaseState


@dataclass
class MergePullRequest(Task):
    @classmethod
    def stage(cls) -> ReleaseStage:
        return ReleaseStage.PULL_REQUEST_MERGED

    def run(self, release: ReleaseState) -> Action:
        github = Manifest.open().get_repository_by_name(self.project.project.repo).github
        pr = find_release_pull_request(self.project, github, state='all')
        if pr is None:
            raise AssertionError('At this stage, the pull request should already exist.')

        if pr.merged:
            success(f'Pull request #{pr.number} is merged.')
            return Action.PROCEED

        if pr.state == 'closed':
            error(f'Pull request #{pr.number} has been closed without merging.',
                  'It needs to be reopened and merged in order to proceed further:', pr.html_url)
            return Action.BREAKPOINT

        if self.can_auto_merge(github, pr):
            if confirm(f'Pull request #{pr.number} can be merged, merge automatically?'):
                result = pr.merge()
                if result.merged:
                    success(f'Merged #{pr.number}.')
                    return Action.PROCEED
                else:
                    error(f'Failed to merge #{pr.number}:', result.message)

        log(f'Pull request #{pr.number} awaits merging.', pr.html_url)
        return Action.BREAKPOINT

    @classmethod
    def can_auto_merge(cls, repo: GithubRepository, pr: PullRequest):
        if not pr.mergeable:
            return False

        status = repo.get_commit(pr.head.sha).get_combined_status()
        if status.state in ('failure', 'error'):
            log('Following statuses failed:',
                ', '.join(s.context for s in status.statuses if s.state in ('failure', 'error')))
            return False
        elif status.state == 'pending' and status.statuses:
            log('Waiting for following statuses:',
                ', '.join(s.context for s in status.statuses if s.state == 'pending'))
            return False

        changes_requested = {review.user.login: review.state == 'CHANGES_REQUESTED'
                             for review in pr.get_reviews()}
        if any(changes_requested.values()):
            log('Changes requested by:', ', '.join(u for u, s in changes_requested.items() if s))
            return False

        return True
