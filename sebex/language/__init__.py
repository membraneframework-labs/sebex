from typing import List, Type

from sebex.analysis.model import Language
from sebex.language.abc import LanguageSupport
from sebex.config.manifest import ProjectHandle


def all_languages() -> List[Type[LanguageSupport]]:
    from sebex.language.elixir import ElixirLanguageSupport

    return [
        ElixirLanguageSupport,
    ]


def detect_language(project: ProjectHandle) -> Language:
    for support in all_languages():
        if support.test_project(project):
            return support.language()

    return Language.UNKNOWN


def language_support_for(language: Language) -> LanguageSupport:
    for support in all_languages():
        if support.language() == language:
            return support()

    raise ValueError(f'No language support for {language}')
