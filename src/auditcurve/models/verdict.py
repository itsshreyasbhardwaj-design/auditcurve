"""MonitorVerdict: what a trusted-monitor strategy produces for one trajectory."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .cost import CostRecord


@dataclass(frozen=True)
class MonitorVerdict:
    verdict_id: str
    strategy_name: str
    trajectory_id: str
    flagged: bool
    confidence: float
    cost_record: CostRecord
    budget: int | None = None
    localized_step_index: int | None = None
    raw_response_text: str = ""
    flagged_at_step_index: int | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["cost_record"] = self.cost_record.to_dict()
        return d

    @staticmethod
    def from_dict(data: dict) -> MonitorVerdict:
        data = dict(data)
        data["cost_record"] = CostRecord.from_dict(data["cost_record"])
        return MonitorVerdict(**data)
