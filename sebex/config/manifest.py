from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple, Dict, Union, Iterable, Type, List, Optional

from git import Repo as GitRepo
from github import Repository as GithubRepository

from sebex.config.file import ConfigFile
from sebex.config.format import Format, YamlFormat
from sebex.context import Context


@dataclass(order=True, unsafe_hash=True)
class RepositoryHandle:
    __slots__ = ['name']

    name: str

    def __init__(self, name: Union[str, 'RepositoryHandle']):
        if isinstance(name, str):
            self.name = name
        else:
            self.name = name.name

    @property
    def location(self) -> Path:
        return Context.current().workspace_path / self.name

    def exists(self) -> bool:
        return self.location.exists()

    @property
    def git(self) -> GitRepo:
        return GitRepo(self.location)

    def __str__(self):
        return self.name


@dataclass(order=True, unsafe_hash=True)
class ProjectHandle:
    __slots__ = ['repo', 'path']

    repo: RepositoryHandle
    path: Path

    def __init__(self, repo: Union['RepositoryHandle', 'ProjectHandle'], path: Path = None):
        if isinstance(repo, self.__class__):
            self.repo = repo.repo
            self.path = repo.path
        else:
            self.repo = repo
            self.path = path

    @classmethod
    def root(cls, repo: Union[str, 'RepositoryHandle']) -> 'ProjectHandle':
        return cls(RepositoryHandle(repo), Path('.'))

    @property
    def is_root(self) -> bool:
        return self.path == Path('.')

    @property
    def location(self) -> Path:
        return self.repo.location / self.path

    def exists(self) -> bool:
        return self.location.exists()

    def __str__(self):
        if not self.is_root:
            return f'{self.repo}:{self.path}'
        else:
            return str(self.repo)


class ProjectManifest(NamedTuple):
    path: Path = Path('.')

    @property
    def is_root(self) -> bool:
        return self.path == Path('.')

    def to_raw(self) -> Dict:
        return {'path': self.path}

    @staticmethod
    def from_raw(raw: Dict) -> 'ProjectManifest':
        return ProjectManifest(path=Path(raw['path']))


class RepositoryManifest(NamedTuple):
    name: str
    remote_url: str
    projects: List[ProjectManifest]

    @property
    def handle(self) -> RepositoryHandle:
        return RepositoryHandle(self.name)

    def project(self, path: str) -> ProjectHandle:
        for project in self.projects:
            if project.path == path:
                return ProjectHandle(repo=self.handle, path=project.path)

        raise KeyError(f'Unknown project: {path}')

    def project_handles(self) -> Iterable[ProjectHandle]:
        for project in self.projects:
            yield ProjectHandle(repo=self.handle, path=project.path)

    @property
    def location(self) -> Path:
        return self.handle.location

    def to_raw(self) -> Dict:
        d = {'name': self.name, 'remote_url': self.remote_url}

        if not (len(self.projects) == 1 and self.projects[0].is_root):
            d['projects'] = [ProjectManifest.to_raw(p) for p in self.projects]

        return d

    @staticmethod
    def from_raw(raw: Dict) -> 'RepositoryManifest':
        projects = [ProjectManifest.from_raw(r) for r in raw.get('projects', [{'path': '.'}])]
        return RepositoryManifest(name=raw['name'], remote_url=raw['remote_url'], projects=projects)

    @staticmethod
    def from_github_repository(repo: GithubRepository) -> 'RepositoryManifest':
        return RepositoryManifest(name=repo.name, remote_url=repo.ssh_url,
                                  projects=[ProjectManifest()])


class Manifest(ConfigFile):
    _name = 'manifest'
    _data = {
        'repositories': []
    }

    _repository_index: Dict[str, int]

    def __init__(self, name: Optional[str], data):
        super().__init__(name, data)

        self._repository_index = {r['name']: i for i, r in enumerate(self._data['repositories'])}

    @classmethod
    def format(cls) -> Type[Format]:
        return YamlFormat

    def get_repository_by_name(self, name: Union[str, RepositoryHandle]) -> RepositoryManifest:
        repo = self.find_repository_by_name(name)

        if repo is None:
            raise Exception(f'Unknown repository "{name}".')

        return repo

    def find_repository_by_name(self, name: Union[str, RepositoryHandle]) -> \
            Optional[RepositoryManifest]:
        name = str(name)

        if name not in self._repository_index:
            return None

        raw = self._data['repositories'][self._repository_index[name]]
        return RepositoryManifest.from_raw(raw)

    def iter_repositories(self) -> Iterable[RepositoryManifest]:
        for raw in self._data['repositories']:
            yield RepositoryManifest.from_raw(raw)

    def upsert_repository(self, repo: RepositoryManifest):
        repos = self._data['repositories']

        if repo.name in self._repository_index:
            repos[self._repository_index[repo.name]] = repo.to_raw()
        else:
            repos.append(repo.to_raw())
            self._repository_index[repo.name] = len(repos) - 1
