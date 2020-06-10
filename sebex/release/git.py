from typing import Optional

from github.PullRequest import PullRequest

from sebex.release.state import ProjectState


def release_branch_name(project: ProjectState) -> str:
    return f'release/{release_tag_name(project)}'


def release_tag_name(project: ProjectState) -> str:
    return f'v{project.to_version}'


def pull_request_title(project: ProjectState) -> str:
    return f'Release {project.project} v{project.to_version}'


def find_release_pull_request(project: ProjectState, **filters) -> Optional[PullRequest]:
    return project.project.repo.vcs.find_pull_request(branch=release_branch_name(project),
                                                      **filters)
