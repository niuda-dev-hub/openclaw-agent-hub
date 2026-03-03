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


class AgentUpdate(BaseModel):
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None


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
    total_score: float
    comments: Optional[str] = None


class EvaluationRead(BaseModel):
    id: str
    task_id: str
    submission_id: str
    reviewer_id: Optional[str] = None
    source: str
    rubric: Dict[str, Any] = Field(default_factory=dict)
    total_score: float
    comments: Optional[str] = None
    created_at: int


class LeaderboardEntry(BaseModel):
    submission_id: str
    avg_score: float
    review_count: int


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
