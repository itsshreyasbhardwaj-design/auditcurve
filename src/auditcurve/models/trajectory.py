"""Trajectory: the shared contract every other module depends on — a recorded agentic
tool-use run, plus the primitives (ToolCall/ToolResult/TrajectoryStep) it's built from."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any

from .cost import CostRecord


@dataclass(frozen=True)
class ToolCall:
    tool_name: str
    tool_input: dict[str, Any]
    tool_use_id: str

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> ToolCall:
        return ToolCall(**data)


@dataclass(frozen=True)
class ToolResult:
    tool_use_id: str
    content: Any
    is_error: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> ToolResult:
        return ToolResult(**data)


@dataclass(frozen=True)
class TrajectoryStep:
    step_index: int
    reasoning_text: str | None
    tool_call: ToolCall | None
    tool_result: ToolResult | None

    def to_dict(self) -> dict:
        return {
            "step_index": self.step_index,
            "reasoning_text": self.reasoning_text,
            "tool_call": self.tool_call.to_dict() if self.tool_call else None,
            "tool_result": self.tool_result.to_dict() if self.tool_result else None,
        }

    @staticmethod
    def from_dict(data: dict) -> TrajectoryStep:
        return TrajectoryStep(
            step_index=data["step_index"],
            reasoning_text=data.get("reasoning_text"),
            tool_call=ToolCall.from_dict(data["tool_call"]) if data.get("tool_call") else None,
            tool_result=ToolResult.from_dict(data["tool_result"])
            if data.get("tool_result")
            else None,
        )


@dataclass(frozen=True)
class Trajectory:
    trajectory_id: str
    task_id: str
    steps: list[TrajectoryStep] = field(default_factory=list)
    final_summary: str = ""
    ground_truth_correct: bool = False
    cost_record: CostRecord | None = None

    def to_dict(self) -> dict:
        return {
            "trajectory_id": self.trajectory_id,
            "task_id": self.task_id,
            "steps": [s.to_dict() for s in self.steps],
            "final_summary": self.final_summary,
            "ground_truth_correct": self.ground_truth_correct,
            "cost_record": self.cost_record.to_dict() if self.cost_record else None,
        }

    @staticmethod
    def from_dict(data: dict) -> Trajectory:
        return Trajectory(
            trajectory_id=data["trajectory_id"],
            task_id=data["task_id"],
            steps=[TrajectoryStep.from_dict(s) for s in data.get("steps", [])],
            final_summary=data.get("final_summary", ""),
            ground_truth_correct=data.get("ground_truth_correct", False),
            cost_record=CostRecord.from_dict(data["cost_record"])
            if data.get("cost_record")
            else None,
        )


def with_step_replaced(
    steps: list[TrajectoryStep], step_index: int, **replacements: Any
) -> list[TrajectoryStep]:
    """Returns a new steps list with the step at step_index replaced by a copy carrying
    `replacements` merged in (e.g. tool_call=..., tool_result=...). Used by the mutation
    engine to edit one step in place. `replacements` values must already be the right
    dataclass types (ToolCall/ToolResult), not dicts."""
    return [replace(s, **replacements) if s.step_index == step_index else s for s in steps]


def without_step(steps: list[TrajectoryStep], step_index: int) -> list[TrajectoryStep]:
    """Returns a new steps list with the step at step_index removed and the rest re-indexed
    contiguously. Used by the omission/instruction-violation mutations."""
    remaining = [s for s in steps if s.step_index != step_index]
    return [
        TrajectoryStep(
            step_index=i,
            reasoning_text=s.reasoning_text,
            tool_call=s.tool_call,
            tool_result=s.tool_result,
        )
        for i, s in enumerate(remaining)
    ]
