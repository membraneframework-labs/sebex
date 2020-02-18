import pytest

from sebex.analysis import VersionRequirement, Version


@pytest.mark.parametrize('requirement_str, version_str, expected', [
    ('1.0.0', '1.0.0', True),
    ('1.0.0', '1.0.1', False),
    ('==1.0.0', '1.0.0', True),
    ('==1.0.0', '1.0.1', False),
    ('!=1.0.0', '1.0.0', False),
    ('!=1.0.0', '1.0.1', True),
    ('>1.0.0', '0.9.0', False),
    ('>1.0.0', '1.0.0', False),
    ('>1.0.0', '1.0.1', True),
    ('>=1.0.0', '0.9.0', False),
    ('>=1.0.0', '1.0.0', True),
    ('>=1.0.0', '1.0.1', True),
    ('<1.0.0', '0.9.0', True),
    ('<1.0.0', '1.0.0', False),
    ('<1.0.0', '1.0.1', False),
    ('<=1.0.0', '0.9.0', True),
    ('<=1.0.0', '1.0.0', True),
    ('<=1.0.0', '1.0.1', False),

    # https://hexdocs.pm/elixir/Version.html#module-requirements, :allow_pre == False
    ('~> 2.0', '2.1.0', True),
    ('~> 2.0', '3.0.0', False),
    ('~> 2.0.0', '2.0.5', True),
    ('~> 2.0.0', '2.1.0', False),
    ('~> 2.1.2', '2.1.6-dev', False),
    ('~> 2.1-dev', '2.2.0-dev', True),
    ('~> 2.1.2-dev', '2.1.6-dev', True),
    ('>= 2.1.0', '2.2.0-dev', False),
    ('>= 2.1.0-dev', '2.2.6-dev', True),
])
def test_version_requirement_match(requirement_str, version_str, expected):
    requirement = VersionRequirement.parse(requirement_str)
    version = Version.parse(version_str)
    assert requirement.match(version) == expected
