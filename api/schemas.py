from typing import Literal

from pydantic import BaseModel

Verdict = Literal["PASS", "AT_RISK", "WILL_FAIL"]
StepResult = Literal["pass", "fail", "warn", "skip"]
Scalar = str | int | float | bool


class TruthValue(BaseModel):
    strength: float
    confidence: float


class TraceStep(BaseModel):
    step: int
    rule: str
    result: StepResult
    fact: str
    reason: str
    values: dict[str, str | int | float]
    stv: tuple[float, float] | None = None
    citation: str
    premises: list[str] = []


class Fix(BaseModel):
    action: str
    action_sw: str
    flips_to: Verdict
    rule: str
    patch: dict[str, Scalar]
    requires_input: bool


class CheckResult(BaseModel):
    claim: str
    verdict: Verdict
    truth_value: TruthValue
    revenue_at_risk_kes: float
    trace: list[TraceStep]
    fixes: list[Fix]
    rulebook_version: str
    trace_hash: str
    prev_hash: str


class Narration(BaseModel):
    language: Literal["en", "sw"]
    text: str
    source: Literal["llm", "template"]
    verdict: Verdict


class Citation(BaseModel):
    rule: str
    name: str
    condition: str
    document: str
    section: str
    url: str
    effective: str
    verified: bool
    quote: str
    note: str
    metta_source: str


class RuleCount(BaseModel):
    rule: str
    name: str
    count: int


class DayActivity(BaseModel):
    date: str
    checks: int
    flagged: int


class Overview(BaseModel):
    days: int
    since: str
    checks: int
    claims: int
    passing: int
    at_risk: int
    will_fail: int
    revenue_at_risk_kes: float
    revenue_protected_kes: float
    claims_protected: int
    top_failing_rules: list[RuleCount]
    daily: list[DayActivity]
