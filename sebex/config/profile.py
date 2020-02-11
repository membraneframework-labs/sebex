from abc import ABC, abstractmethod
from typing import Iterable, Union, List, Type

from sebex.config.file import ConfigFile
from sebex.config.format import Format, LinesFormat
from sebex.config.manifest import RepositoryManifest, Manifest, RepositoryHandle, ProjectHandle
from sebex.context import Context
from sebex.smartmatch import Pattern

PROFILE_PREFIX = 'profiles/'


class Profile(ABC):
    @abstractmethod
    def apply(self, manifest: Manifest) -> Iterable[RepositoryManifest]:
        pass


class AllProfile(Profile):
    def apply(self, manifest: Manifest) -> Iterable[RepositoryManifest]:
        return manifest.iter_repositories()


class UserDefinedProfile(ConfigFile, Profile):
    _data: List[str]
    _index: Pattern

    @classmethod
    def format(cls) -> Type[Format]:
        return LinesFormat

    def __init__(self, name: Union[str, None], data):
        assert name is not None and name.startswith(PROFILE_PREFIX), \
            f'Profile name must be provided, and it must start with "{PROFILE_PREFIX}"'

        super().__init__(name, data)

        if self._data is None:
            raise Exception(f'Failed to load {name}, maybe the profile file is missing?')

        if not isinstance(self._data, list):
            raise Exception('User defined profile must be an array of repository names.')

        for name in self._data:
            if not isinstance(name, str):
                raise Exception('User defined profile must be an array of repository names.')

        self._index = Pattern.compile(self._data)

    def apply(self, manifest: Manifest) -> Iterable[RepositoryManifest]:
        for repo_manifest in manifest.iter_repositories():
            if self._index.match(repo_manifest.name):
                yield repo_manifest


def get_profile_by_name(name: str) -> Profile:
    if name == 'all':
        return AllProfile()
    else:
        return UserDefinedProfile.open(f'{PROFILE_PREFIX}/{name}')


def current_profile() -> Profile:
    return get_profile_by_name(Context.current().profile_name)


def current_repositories() -> Iterable[RepositoryManifest]:
    profile = current_profile()
    manifest = Manifest.open()
    return profile.apply(manifest)


def current_repository_handles() -> Iterable[RepositoryHandle]:
    for manifest in current_repositories():
        yield manifest.handle


def current_project_handles() -> Iterable[ProjectHandle]:
    for manifest in current_repositories():
        yield from manifest.project_handles()
