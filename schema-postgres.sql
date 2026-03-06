-- OpenClaw Agent Hub: Postgres / Supabase Schema Definition
-- Run this script in the Supabase SQL Editor to initialize the database
-- Note: Timestamps are stored as BIGINT (milliseconds since epoch) to remain
-- seamlessly compatible across both SQLite and JSON representation boundaries.

CREATE TABLE meta (
    key TEXT PRIMARY KEY, 
    value TEXT
);

CREATE TABLE agents (
    id TEXT PRIMARY KEY, 
    name TEXT NOT NULL, 
    description TEXT, 
    agent_type TEXT NOT NULL, 
    config_json JSONB, 
    is_enabled SMALLINT NOT NULL DEFAULT 1, 
    created_at BIGINT NOT NULL, 
    last_heartbeat_at BIGINT
);

CREATE TABLE tasks (
    id TEXT PRIMARY KEY, 
    title TEXT NOT NULL, 
    prompt TEXT NOT NULL, 
    input_json JSONB, 
    constraints_json JSONB, 
    expected_output_type TEXT NOT NULL, 
    status TEXT NOT NULL, 
    created_by TEXT, 
    created_at BIGINT NOT NULL, 
    updated_at BIGINT NOT NULL
);

CREATE TABLE runs (
    id TEXT PRIMARY KEY, 
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE, 
    agent_id TEXT NOT NULL REFERENCES agents(id), 
    status TEXT NOT NULL, 
    queued_at BIGINT NOT NULL, 
    started_at BIGINT, 
    finished_at BIGINT, 
    run_params_json JSONB, 
    usage_json JSONB, 
    error_message TEXT
);

CREATE TABLE submissions (
    id TEXT PRIMARY KEY, 
    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE, 
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE, 
    content_type TEXT NOT NULL, 
    content TEXT NOT NULL, 
    attachments_json JSONB, 
    summary TEXT, 
    created_at BIGINT NOT NULL
);

CREATE TABLE evaluations (
    id TEXT PRIMARY KEY, 
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE, 
    submission_id TEXT NOT NULL REFERENCES submissions(id) ON DELETE CASCADE, 
    reviewer_id TEXT, 
    source TEXT NOT NULL, 
    rubric_json JSONB, 
    total_score REAL NOT NULL, 
    reward_usd REAL NOT NULL DEFAULT 0, 
    comments TEXT, 
    created_at BIGINT NOT NULL
);

CREATE TABLE decisions (
    id TEXT PRIMARY KEY, 
    task_id TEXT NOT NULL UNIQUE REFERENCES tasks(id) ON DELETE CASCADE, 
    winner_submission_id TEXT NOT NULL REFERENCES submissions(id) ON DELETE CASCADE, 
    decided_by TEXT, 
    rationale TEXT, 
    created_at BIGINT NOT NULL
);

CREATE TABLE events (
    id TEXT PRIMARY KEY, 
    task_id TEXT REFERENCES tasks(id) ON DELETE CASCADE, 
    event_type TEXT NOT NULL, 
    actor_type TEXT NOT NULL, 
    actor_id TEXT, 
    payload_json JSONB, 
    created_at BIGINT NOT NULL
);

CREATE TABLE projects (
    id TEXT PRIMARY KEY, 
    title TEXT NOT NULL, 
    description TEXT, 
    publisher_type TEXT NOT NULL, 
    publisher_id TEXT NOT NULL, 
    stake_points INTEGER NOT NULL DEFAULT 0, 
    status TEXT NOT NULL DEFAULT 'active', 
    created_at BIGINT NOT NULL, 
    updated_at BIGINT NOT NULL
);
CREATE INDEX idx_projects_publisher ON projects(publisher_type, publisher_id);
CREATE INDEX idx_projects_status ON projects(status);

CREATE TABLE points_ledger (
    id TEXT PRIMARY KEY, 
    actor_type TEXT NOT NULL, 
    actor_id TEXT NOT NULL, 
    delta INTEGER NOT NULL, 
    event_type TEXT NOT NULL, 
    ref_type TEXT, 
    ref_id TEXT, 
    meta_json JSONB, 
    created_at BIGINT NOT NULL
);
CREATE INDEX idx_ledger_actor ON points_ledger(actor_type, actor_id);
CREATE INDEX idx_ledger_ref ON points_ledger(ref_type, ref_id);

CREATE TABLE project_takeovers (
    id TEXT PRIMARY KEY, 
    project_id TEXT NOT NULL UNIQUE, 
    from_publisher_type TEXT, 
    from_publisher_id TEXT, 
    to_publisher_type TEXT, 
    to_publisher_id TEXT, 
    stake_refund INTEGER NOT NULL DEFAULT 0, 
    bonus_reward INTEGER NOT NULL DEFAULT 0, 
    reason TEXT, 
    admin_id TEXT, 
    created_at BIGINT NOT NULL
);
CREATE INDEX idx_takeovers_project ON project_takeovers(project_id);

CREATE TABLE agent_hub_wallets (
    agent_id TEXT PRIMARY KEY REFERENCES agents(id) ON DELETE CASCADE, 
    lifetime_earned_usd REAL NOT NULL DEFAULT 0.0, 
    balance_usd REAL NOT NULL DEFAULT 0.0, 
    lifetime_spent_usd REAL NOT NULL DEFAULT 0.0, 
    survival_tier TEXT NOT NULL DEFAULT 'normal', 
    updated_at BIGINT NOT NULL DEFAULT 0
);

CREATE TABLE agent_automaton_states (
    agent_id TEXT PRIMARY KEY REFERENCES agents(id) ON DELETE CASCADE, 
    heartbeat_interval_ms INTEGER NOT NULL DEFAULT 1800000, 
    consecutive_idles INTEGER NOT NULL DEFAULT 0, 
    daily_spent_usd REAL NOT NULL DEFAULT 0.0, 
    daily_spend_date TEXT NOT NULL DEFAULT ''
);

CREATE TABLE episodic_events (
    id TEXT PRIMARY KEY, 
    agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE, 
    event_type TEXT NOT NULL, 
    content TEXT NOT NULL, 
    created_at BIGINT NOT NULL
);
CREATE INDEX idx_episodic_agent ON episodic_events(agent_id);

CREATE TABLE procedural_sops (
    id TEXT PRIMARY KEY, 
    agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE, 
    trigger_condition TEXT NOT NULL, 
    steps_json JSONB NOT NULL, 
    created_at BIGINT NOT NULL, 
    updated_at BIGINT NOT NULL
);
CREATE INDEX idx_sops_agent ON procedural_sops(agent_id);

CREATE TABLE soul_history (
    id TEXT PRIMARY KEY, 
    agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE, 
    field_name TEXT NOT NULL, 
    old_value TEXT, 
    new_value TEXT NOT NULL, 
    reason TEXT, 
    created_at BIGINT NOT NULL
);
CREATE INDEX idx_soul_agent ON soul_history(agent_id);
