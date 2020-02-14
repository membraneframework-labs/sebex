from sebex.analysis import AnalysisDatabase
from sebex.analysis.database import _Projects


class MockAnalysisDatabase(AnalysisDatabase):
    @classmethod
    def mock(cls, projects: _Projects) -> 'MockAnalysisDatabase':
        return cls._analyze(projects)
