from sebex.release import ProjectState


def release_branch_name(project: ProjectState) -> str:
    return f'release/v{project.to_version}'
