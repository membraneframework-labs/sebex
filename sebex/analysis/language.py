from enum import Enum
from typing import TYPE_CHECKING

from sebex.analysis.analyzer import Analyzer
from sebex.analysis.elixir import mix_file, ElixirAnalyzer

if TYPE_CHECKING:
    from sebex.config import ProjectHandle


class Language(Enum):
    ELIXIR = 'elixir'
    UNKNOWN = 'unknown'

    @classmethod
    def detect(cls, project: 'ProjectHandle') -> 'Language':
        if mix_file(project).exists():
            return cls.ELIXIR

        return cls.UNKNOWN

    @property
    def analyzer(self) -> Analyzer:
        if self == self.ELIXIR:
            return ElixirAnalyzer()

        raise KeyError(f'There is no analyzer for language: {self.value}')
