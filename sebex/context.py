from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

from github import Github

METADATA_DIRECTORY_NAME = '.sebex'

_context_var = ContextVar('sebex_context')


class Context:
    workspace_path: Path
    profile_name: str
    github: Github
    jobs: int

    def __init__(self, workspace: str, profile: str, github_access_token: str, jobs: int) -> None:
        self.workspace_path = Path(workspace)
        self.profile_name = profile
        self.github = Github(github_access_token)
        self.jobs = jobs

    @classmethod
    def current(cls) -> 'Context':
        return _context_var.get()

    @classmethod
    def initial(cls, *args, **kwargs):
        _context_var.set(cls(*args, **kwargs))

    @classmethod
    @contextmanager
    def activate(cls, instance: 'Context'):
        token = _context_var.set(instance)
        try:
            yield _context_var.get()
        finally:
            _context_var.reset(token)

    @property
    def meta_path(self) -> Path:
        return self.workspace_path / METADATA_DIRECTORY_NAME
