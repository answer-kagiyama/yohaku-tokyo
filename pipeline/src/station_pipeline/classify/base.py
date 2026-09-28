"""SemanticClassifier (ADR 0003, spec 0009 §7). Rules stay the default; a classifier only helps
where the rules cannot decide. Judgements always carry the classifier name and model version."""

from dataclasses import asdict, dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class DatasetDescriptor:
    name: str
    organization: str | None
    resources: list[str]
    columns: list[str]


@dataclass(frozen=True)
class FacilityDescriptor:
    name: str
    categories: list[str] = field(default_factory=list)
    source: str = ""


@dataclass(frozen=True)
class Judgement:
    category: str  # a feature key or "none"
    confidence: float
    classifier: str
    model: str | None
    list_score: float | None = None  # datasets only: "a list of places, one per row"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["listScore"] = d.pop("list_score")
        return d


class SemanticClassifier(Protocol):
    name: str

    def judge_dataset(self, dataset: DatasetDescriptor) -> Judgement: ...

    def judge_facilities(self, facilities: list[FacilityDescriptor]) -> list[Judgement]: ...
