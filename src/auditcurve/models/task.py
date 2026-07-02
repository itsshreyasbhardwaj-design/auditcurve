"""Task: a domain-specific tool-use scenario for the untrusted agent to solve, plus its
policy constraints and ground-truth evaluator."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .trajectory import Trajectory


@dataclass(frozen=True)
class ToolSchema:
    name: str
    description: str
    input_schema: dict[str, Any]

    def to_anthropic_tool(self) -> dict[str, Any]:
        """Renders this schema in the exact shape the Anthropic Messages API expects."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


@dataclass(frozen=True)
class PolicyConstraint:
    id: str
    description: str


@dataclass(frozen=True)
class EvaluationResult:
    correct: bool
    reason: str


@dataclass(frozen=True)
class Task:
    task_id: str
    domain: str
    title: str
    initial_state: dict[str, Any]
    tool_schemas: list[ToolSchema]
    policy_constraints: list[PolicyConstraint]
    user_request: str
    system_prompt: str
    evaluator: Callable[[Trajectory, dict[str, Any]], EvaluationResult] = field(repr=False)

    def anthropic_tools(self) -> list[dict[str, Any]]:
        return [t.to_anthropic_tool() for t in self.tool_schemas]
