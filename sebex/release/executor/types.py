import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import ClassVar, Optional

import click

from sebex.release.state import ProjectState, ReleaseStage, ReleaseState


class Action(Enum):
    PROCEED = auto()
    BREAKPOINT = auto()
    FINISH = auto()

    def report(self) -> Optional[str]:
        if self == self.PROCEED:
            return None
        elif self == self.BREAKPOINT:
            return click.style('BREAKPOINT', fg='yellow')
        elif self == self.FINISH:
            return click.style('FINISHED', fg='cyan')
        else:
            assert False, 'unreachable'


@dataclass
class Task(ABC):
    project: ProjectState

    @abstractmethod
    def stage(self) -> ReleaseStage:
        """The stage the project will enter after completing this task."""
        ...

    @abstractmethod
    def run(self, release: ReleaseState) -> Action:
        """Execute this task and return action to perform after."""
        ...

    @property
    def human_name(self) -> str:
        return re.sub(r'[A-Z]', r' \g<0>', self.__class__.__name__).strip()
