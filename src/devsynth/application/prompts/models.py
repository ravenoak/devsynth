"""Typed models for prompt auto-tuning components."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, TypedDict
from collections.abc import Iterator, MutableMapping, Sequence

from typing import Literal


class StoredPromptVariant(TypedDict):
    """Serialized representation of :class:`PromptVariant`."""

    variant_id: str
    template: str
    usage_count: int
    success_count: int
    failure_count: int
    feedback_scores: list[float]
    last_used: str | None


SelectionStrategyName = Literal["performance", "exploration", "random"]


@dataclass
class SelectionStrategyConfig:
    """Configuration describing how prompt variants should be selected."""

    name: SelectionStrategyName = "performance"
    exploration_rate: float = 0.2

    def validate(self) -> None:
        """Validate the configuration values."""

        if not 0.0 <= self.exploration_rate <= 1.0:
            msg = "exploration_rate must be between 0.0 and 1.0"
            raise ValueError(msg)


@dataclass
class PromptVariant:
    """Represents a variant of a prompt template with performance metrics."""

    template: str
    variant_id: str | None = None
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    feedback_scores: list[float] = field(default_factory=list)
    last_used: str | None = None

    def __post_init__(self) -> None:
        if self.variant_id is None:
            self.variant_id = hashlib.sha256(self.template.encode()).hexdigest()[:8]

    @property
    def success_rate(self) -> float:
        """Calculate the success rate of this prompt variant."""

        if self.usage_count == 0:
            return 0.0
        return self.success_count / self.usage_count

    @property
    def average_feedback_score(self) -> float:
        """Calculate the average feedback score of this prompt variant."""

        if not self.feedback_scores:
            return 0.0
        return sum(self.feedback_scores) / len(self.feedback_scores)

    @property
    def performance_score(self) -> float:
        """Calculate the overall performance score of this prompt variant."""

        success_weight = 0.7
        feedback_weight = 0.3
        return (success_weight * self.success_rate) + (
            feedback_weight * self.average_feedback_score
        )

    def record_usage(
        self, success: bool | None = None, feedback_score: float | None = None
    ) -> None:
        """Record usage of this prompt variant."""

        self.usage_count += 1
        self.last_used = datetime.now().isoformat()

        if success is not None:
            if success:
                self.success_count += 1
            else:
                self.failure_count += 1

        if feedback_score is not None:
            self.feedback_scores.append(feedback_score)

    def to_dict(self) -> StoredPromptVariant:
        """Convert the prompt variant to a :class:`StoredPromptVariant`."""

        return {
            "variant_id": self.variant_id or "",
            "template": self.template,
            "usage_count": self.usage_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "feedback_scores": list(self.feedback_scores),
            "last_used": self.last_used,
        }

    @classmethod
    def from_dict(cls, data: StoredPromptVariant) -> PromptVariant:
        """Create a prompt variant from a :class:`StoredPromptVariant`."""

        return cls(
            template=data["template"],
            variant_id=data["variant_id"],
            usage_count=data["usage_count"],
            success_count=data["success_count"],
            failure_count=data["failure_count"],
            feedback_scores=list(data["feedback_scores"]),
            last_used=data["last_used"],
        )


@dataclass
class PromptVariantCollection(MutableMapping[str, list[PromptVariant]]):
    """Typed collection of prompt variants keyed by template id."""

    variants_by_template: dict[str, list[PromptVariant]] = field(default_factory=dict)

    def __getitem__(self, key: str) -> list[PromptVariant]:
        return self.variants_by_template[key]

    def __setitem__(
        self, key: str, value: Sequence[PromptVariant]
    ) -> None:  # pragma: no cover - trivial
        self.variants_by_template[key] = list(value)

    def __delitem__(self, key: str) -> None:  # pragma: no cover - unused
        del self.variants_by_template[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.variants_by_template)

    def __len__(self) -> int:
        return len(self.variants_by_template)

    def add_variant(self, template_id: str, variant: PromptVariant) -> None:
        """Add a prompt variant for the given template id."""

        self.variants_by_template.setdefault(template_id, []).append(variant)

    def ensure_template(self, template_id: str) -> None:
        """Ensure a template entry exists for the given id."""

        self.variants_by_template.setdefault(template_id, [])

    def total_variants(self) -> int:
        """Return the total number of variants stored."""

        return sum(len(variants) for variants in self.variants_by_template.values())
