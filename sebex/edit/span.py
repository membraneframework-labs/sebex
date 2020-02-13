from typing import NamedTuple, Dict


class Span(NamedTuple):
    start_line: int
    start_column: int
    end_line: int
    end_column: int

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
