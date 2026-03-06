from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# Agents
class AgentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    agent_type: str = "openclaw"
    config: Dict[str, Any] = Field(default_factory=dict)


class AgentRead(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    agent_type: str
    config: Dict[str, Any] = Field(default_factory=dict)
    is_enabled: bool = True
    created_at: int
    # last_heartbeat_at 为 None 表示从未上报心跳
    last_heartbeat_at: Optional[int] = None


class AgentUpdate(BaseModel):
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None


# Projects
class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = None
    # publisher can be agent/user; v0.1 default uses agent for created_by
    publisher_type: str = "agent"  # agent/user
    publisher_id: str
    stake_points: int = 0


class ProjectRead(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    publisher_type: str
    publisher_id: str
    stake_points: int
    status: str
    created_at: int
    updated_at: int


class AdminProjectTakeover(BaseModel):
    # decision from user:
    # 1) bonus from system treasury (mint) -> no admin balance checks in v0.1
    bonus_reward: int = 0
    reason: Optional[str] = None
    idempotency_key: Optional[str] = None
    # allow admin to identify themselves (simple v0.1; auth later)
    admin_id: str = "admin"


class ProjectTakeoverRead(BaseModel):
    id: str
    project_id: str
    from_publisher_type: Optional[str] = None
    from_publisher_id: Optional[str] = None
    to_publisher_type: Optional[str] = None
    to_publisher_id: Optional[str] = None
    stake_refund: int
    bonus_reward: int
    reason: Optional[str] = None
    admin_id: Optional[str] = None
    created_at: int


# Tasks
class TaskCreate(BaseModel):
    title: str
    prompt: str
    input: Dict[str, Any] = Field(default_factory=dict)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    expected_output_type: str = "text"
    created_by: Optional[str] = None


class TaskRead(BaseModel):
    id: str
    title: str
    prompt: str
    input: Dict[str, Any] = Field(default_factory=dict)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    expected_output_type: str
    status: str
    created_by: Optional[str] = None
    created_at: int
    updated_at: int


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    prompt: Optional[str] = None
    input: Optional[Dict[str, Any]] = None
    constraints: Optional[Dict[str, Any]] = None
    expected_output_type: Optional[str] = None
    status: Optional[str] = None


class TaskStart(BaseModel):
    agent_ids: List[str]
    run_params: Dict[str, Any] = Field(default_factory=dict)


class TaskClaim(BaseModel):
    agent_id: str
    run_params: Dict[str, Any] = Field(default_factory=dict)


class ParticipantEntry(BaseModel):
    agent_id: str
    agent_name: Optional[str] = None
    latest_status: Optional[str] = None
    runs_count: int = 0


# Runs
class RunRead(BaseModel):
    id: str
    task_id: str
    agent_id: str
    status: str
    queued_at: Optional[int] = None
    started_at: Optional[int] = None
    finished_at: Optional[int] = None
    run_params: Dict[str, Any] = Field(default_factory=dict)
    usage: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None


# Submissions
class SubmissionCreate(BaseModel):
    content_type: str = "text"
    content: str
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Optional[str] = None


class SubmissionRead(BaseModel):
    id: str
    run_id: str
    task_id: str
    content_type: str
    content: str
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Optional[str] = None
    created_at: int


# Evaluations
class EvaluationCreate(BaseModel):
    submission_id: str
    reviewer_id: Optional[str] = None
    source: str = "human"  # human/auto
    rubric: Dict[str, Any] = Field(default_factory=dict)
    reward_usd: float  # 任务奖励（美元），原字段 total_score
    comments: Optional[str] = None


class EvaluationRead(BaseModel):
    id: str
    task_id: str
    submission_id: str
    reviewer_id: Optional[str] = None
    source: str
    rubric: Dict[str, Any] = Field(default_factory=dict)
    reward_usd: float
    comments: Optional[str] = None
    created_at: int


class LeaderboardEntry(BaseModel):
    submission_id: str
    avg_reward_usd: float  # 平均奖励（USD）
    review_count: int


# Wallet
class WalletState(BaseModel):
    balance_usd: float
    lifetime_spent_usd: float
    lifetime_earned_usd: float
    survival_tier: str  # high/normal/low_compute/critical/dead

class FundRequest(BaseModel):
    amount_usd: float
    memo: Optional[str] = None


# Decision
class DecisionCreate(BaseModel):
    winner_submission_id: str
    decided_by: Optional[str] = None
    rationale: Optional[str] = None


class DecisionRead(BaseModel):
    id: str
    task_id: str
    winner_submission_id: str
    decided_by: Optional[str] = None
    rationale: Optional[str] = None
    created_at: int


# 审计事件
class EventRead(BaseModel):
    id: str
    task_id: Optional[str] = None
    event_type: str
    actor_type: str
    actor_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: int


# =====================================================================
# Automaton SaaS - Agent State & Memory
# =====================================================================

class AutomatonState(BaseModel):
    agent_id: str
    balance_usd: float
    lifetime_spent_usd: float
    survival_tier: str
    heartbeat_interval_ms: int
    consecutive_idles: int
    daily_spent_usd: float
    daily_spend_date: str


class EpisodicEventCreate(BaseModel):
    event_type: str
    content: str


class EpisodicEventRead(BaseModel):
    id: str
    agent_id: str
    event_type: str
    content: str
    created_at: int


class ProceduralSOPCreate(BaseModel):
    trigger_condition: str
    steps_json: str


class ProceduralSOPRead(BaseModel):
    id: str
    agent_id: str
    trigger_condition: str
    steps_json: str
    created_at: int
    updated_at: int


class SoulHistoryCreate(BaseModel):
    field_name: str
    old_value: Optional[str] = None
    new_value: str
    reason: Optional[str] = None


class SoulHistoryRead(BaseModel):
    id: str
    agent_id: str
    field_name: str
    old_value: Optional[str] = None
    new_value: str
    reason: Optional[str] = None
    created_at: int
