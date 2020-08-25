from dataclasses import dataclass
from enum import IntEnum
from typing import Optional, Iterable, Tuple, Set


class NameSimilarity(IntEnum):
    EXACT = 0
    WHITESPACE_DIFFERENCES = 1
    PUNCTUATION_DIFFERENCES = 2
    DIFFERENT = 10

    def __str__(self):
        return self.name.replace("_", " ").lower()


@dataclass
class NameSimilarityProfile:
    tolerate_whitespace: Optional[str] = " \n\t"
    tolerate_punctuation_marks: Optional[str] = None


REPO_NAME_SIMILARITY = NameSimilarityProfile(tolerate_punctuation_marks="-_. ")


def are_names_similar(a: str, b: str, profile: NameSimilarityProfile) -> NameSimilarity:
    if a == b:
        return NameSimilarity.EXACT

    if profile.tolerate_whitespace:
        a = a.strip(profile.tolerate_whitespace)
        b = b.strip(profile.tolerate_whitespace)

        if a == b:
            return NameSimilarity.WHITESPACE_DIFFERENCES

    if profile.tolerate_punctuation_marks:
        a = str([c for c in a if c not in profile.tolerate_punctuation_marks])
        b = str([c for c in b if c not in profile.tolerate_punctuation_marks])

        if a == b:
            return NameSimilarity.PUNCTUATION_DIFFERENCES

    return NameSimilarity.DIFFERENT


def is_name_similar_to_one_of(
    needle: str, haystack: Iterable[str],
    profile: NameSimilarityProfile
) -> Tuple[NameSimilarity, Optional[str]]:
    best_sim, best_name = NameSimilarity.DIFFERENT, None

    for candidate in haystack:
        sim = are_names_similar(needle, candidate, profile)

        if sim < best_sim:
            best_sim = sim
            best_name = candidate

        if sim == NameSimilarity.EXACT:
            break

    return best_sim, best_name


def find_similar_name_clashes(
    haystack: Set[str],
    profile: NameSimilarityProfile
) -> Iterable[Tuple[str, str, NameSimilarity]]:
    yielded = set()
    for needle in haystack:
        this_haystack = haystack.difference({needle})
        sim, candidate = is_name_similar_to_one_of(needle, this_haystack, profile)
        if sim not in [NameSimilarity.EXACT, NameSimilarity.DIFFERENT] and candidate not in yielded:
            yield needle, candidate, sim
            yielded.add(needle)
