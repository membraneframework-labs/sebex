from dataclasses import dataclass
from typing import Dict, ClassVar, Tuple


@dataclass(order=True, frozen=True)
class Span:
    start_line: int
    start_column: int
    end_line: int
    end_column: int

    ZERO: ClassVar['Span']

    @property
    def start(self) -> Tuple[int, int]:
        return self.start_line, self.start_column

    @property
    def end(self) -> Tuple[int, int]:
        return self.end_line, self.end_column

    def to_raw(self) -> Dict:
        return {
            'start_line': self.start_line,
            'start_column': self.start_column,
            'end_line': self.end_line,
            'end_column': self.end_column,
        }

    @staticmethod
    def from_raw(raw: Dict) -> 'Span':
        return Span(
            start_line=raw['start_line'],
            start_column=raw['start_column'],
            end_line=raw['end_line'],
            end_column=raw['end_column']
        )

    def __str__(self):
        return f'{self.start_line}:{self.start_column} - {self.end_line}:{self.end_column}'


Span.ZERO = Span(0, 0, 0, 0)
