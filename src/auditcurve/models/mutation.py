"""Mutation/MutatedTrajectory: the ground-truth label carrier. Monitors only ever receive
a bare Trajectory (never MutatedTrajectory) — enforced by function signatures throughout
the codebase, not just by convention."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum

from .trajectory import Trajectory


class ErrorType(str, Enum):
    TOOL_MISUSE = "tool_misuse"
    SILENT_NUMERIC_ERROR = "silent_numeric_error"
    OMISSION = "omission"
    FABRICATION = "fabrication"
    INSTRUCTION_VIOLATION = "instruction_violation"


class Severity(str, Enum):
    BLATANT = "blatant"
    SUBTLE = "subtle"


@dataclass(frozen=True)
class Mutation:
    mutation_id: str
    error_type: ErrorType
    severity: Severity
    target_step_index: int
    description: str
    original_trajectory_id: str

    def to_dict(self) -> dict:
        d = asdict(self)
        d["error_type"] = self.error_type.value
        d["severity"] = self.severity.value
        return d

    @staticmethod
    def from_dict(data: dict) -> Mutation:
        return Mutation(
            mutation_id=data["mutation_id"],
            error_type=ErrorType(data["error_type"]),
            severity=Severity(data["severity"]),
            target_step_index=data["target_step_index"],
            description=data["description"],
            original_trajectory_id=data["original_trajectory_id"],
        )


@dataclass(frozen=True)
class MutatedTrajectory:
    trajectory: Trajectory
    mutation: Mutation | None
    is_mutated: bool

    def to_dict(self) -> dict:
        return {
            "trajectory": self.trajectory.to_dict(),
            "mutation": self.mutation.to_dict() if self.mutation else None,
            "is_mutated": self.is_mutated,
        }

    @staticmethod
    def from_dict(data: dict) -> MutatedTrajectory:
        return MutatedTrajectory(
            trajectory=Trajectory.from_dict(data["trajectory"]),
            mutation=Mutation.from_dict(data["mutation"]) if data.get("mutation") else None,
            is_mutated=data["is_mutated"],
        )
