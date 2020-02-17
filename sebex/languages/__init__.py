from typing import List, Type

from sebex.analysis.types import LanguageSupport, Language
from sebex.config import ProjectHandle
from sebex.languages.elixir import ElixirLanguageSupport

ALL_LANGUAGES: List[Type[LanguageSupport]] = [
    ElixirLanguageSupport
]


def detect_language(project: ProjectHandle) -> Language:
    for support in ALL_LANGUAGES:
        if support.test_project(project):
            return support.language()

    return Language.UNKNOWN


def language_support_for(language: Language) -> LanguageSupport:
    for support in ALL_LANGUAGES:
        if support.language() == language:
            return support()

    raise ValueError(f'No language support for {language}')
