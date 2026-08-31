from __future__ import annotations

from typing import Any, Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from research.early_risk.common import canonical_json_bytes, sha256_bytes


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class E0Report(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_id: NonEmptyText
    report_version: Literal["1.0.0"] = "1.0.0"
    evidence_level: Literal["E0"] = "E0"
    prediction_evidence: Literal[False] = False
    deployment_approved: Literal[False] = False
    generated_from: tuple[NonEmptyText, ...] = Field(min_length=1)
    claims: tuple[NonEmptyText, ...] = Field(min_length=1)
    limitations: tuple[NonEmptyText, ...] = Field(min_length=1)
    results: dict[str, Any]

    @model_validator(mode="after")
    def enforce_truth_boundary(self) -> "E0Report":
        combined = "\n".join(self.claims)
        forbidden = (
            "已经能提前预测",
            "已实现提前预警",
            "临床级准确率",
            "自动救援已启用",
        )
        if any(phrase in combined for phrase in forbidden):
            raise ValueError("E0 报告包含越级能力声明。")
        return self


def report_sha256(report: E0Report) -> str:
    return sha256_bytes(canonical_json_bytes(report.model_dump(mode="json")))
