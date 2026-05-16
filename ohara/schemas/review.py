from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RiskLevel = Literal["low", "medium", "high", "critical"]
Severity = Literal["low", "medium", "high", "critical"]
Confidence = Literal["high", "medium", "low"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReviewFinding(StrictModel):
    title: str = ""
    severity: Severity = "medium"
    evidence: list[str] = Field(default_factory=list)
    impact: str = ""
    recommendation: str = ""
    codex_hint: str = ""
    confidence: Confidence
    source_paths: list[str]


class ImplementationStep(StrictModel):
    order: int = 0
    title: str = ""
    rationale: str = ""
    files_or_areas: list[str] = Field(default_factory=list)
    validation: list[str] = Field(default_factory=list)


class QuickWin(StrictModel):
    title: str = ""
    expected_value: str = ""
    effort: Literal["small", "medium", "large"] = "small"


class CodexAction(StrictModel):
    action: str = ""
    target: str = ""
    instructions: str = ""
    acceptance_criteria: list[str] = Field(default_factory=list)


class ExecutionOrderItem(StrictModel):
    order: int = 0
    action: str = ""
    depends_on: list[str] = Field(default_factory=list)


class ReviewOutput(StrictModel):
    template: str
    summary: str
    overall_risk: RiskLevel
    critical_issues: list[ReviewFinding]
    technical_debt: list[ReviewFinding]
    security_risks: list[ReviewFinding]
    scalability_issues: list[ReviewFinding]
    architecture_feedback: list[ReviewFinding]
    implementation_plan: list[ImplementationStep]
    quick_wins: list[QuickWin]
    codex_actions: list[CodexAction]
    recommended_execution_order: list[ExecutionOrderItem]
