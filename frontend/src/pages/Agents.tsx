/**
 * Agents - Agent 管理页面
 * 显示所有 Agent 的卡片，包含在线状态、类型、最近心跳，支持启用/禁用。
 */
import { useEffect, useState, useCallback } from 'react'
import { apiGet, apiPatch } from '../api/client'
import { AgentStatusBadge } from '../components/AgentStatusBadge'
import { useI18n } from '../i18n'
import { fmtTime } from '../lib/format'

interface AgentRead {
    id: string
    name: string
    description?: string | null
    agent_type: string
    is_enabled: boolean
    created_at: number
    last_heartbeat_at?: number | null
}

export function Agents() {
    const { t } = useI18n()
    const [agents, setAgents] = useState<AgentRead[]>([])
    const [loading, setLoading] = useState(true)
    const [err, setErr] = useState('')
    const [toggling, setToggling] = useState<string | null>(null)

    const load = useCallback(() => {
        setLoading(true)
        apiGet<AgentRead[]>('/api/v0.1/agents')
            .then(setAgents)
            .catch((e) => setErr(String(e)))
            .finally(() => setLoading(false))
    }, [])

    useEffect(() => { load() }, [load])

    const toggleEnable = async (agent: AgentRead) => {
        setToggling(agent.id)
        try {
            await apiPatch(`/api/v0.1/agents/${agent.id}`, { is_enabled: !agent.is_enabled })
            load()
        } catch (e) {
            setErr(String(e))
        } finally {
            setToggling(null)
        }
    }

    return (
        <div style={{ display: 'grid', gap: 16 }}>
            <div className="panel-header" style={{ margin: 0, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div className="h1" style={{ margin: 0 }}>{t.agents.title}</div>
                <button className="btn" onClick={load} style={{ fontSize: 12 }}>↺ {t.common.refresh}</button>
            </div>

            {err && <div className="error">{err}</div>}

            {loading
                ? <div style={{ color: 'var(--muted)' }}>{t.common.loading}</div>
                : agents.length === 0
                    ? <div style={{ color: 'var(--muted)' }}>{t.common.noData}</div>
                    : (
                        <div className="agents-grid">
                            {agents.map((a) => (
                                <div key={a.id} className="agent-card" style={{ opacity: a.is_enabled ? 1 : 0.6 }}>
                                    {/* 左侧状态指示 */}
                                    <div style={{ paddingTop: 2 }}>
                                        <AgentStatusBadge lastHeartbeatAt={a.last_heartbeat_at} showLabel={false} />
                                    </div>

                                    {/* 主体信息 */}
                                    <div className="agent-card-body">
                                        <div className="agent-card-name">{a.name}</div>
                                        <div className="agent-card-meta">
                                            {a.agent_type}
                                            {a.description && <span> · {a.description}</span>}
                                        </div>

                                        <div style={{ marginTop: 8, display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
                                            {/* 在线状态徽章（带文字） */}
                                            <AgentStatusBadge lastHeartbeatAt={a.last_heartbeat_at} />

                                            {/* 启用状态 */}
                                            <span className={`badge ${a.is_enabled ? 'ok' : ''}`}>
                                                {a.is_enabled ? t.common.enabled : t.common.disabled}
                                            </span>
                                        </div>

                                        <div style={{ marginTop: 6, color: 'var(--muted)', fontSize: 11 }}>
                                            {t.agents.colLastSeen}: {a.last_heartbeat_at ? fmtTime(a.last_heartbeat_at) : t.agents.neverSeen}
                                        </div>
                                    </div>

                                    {/* 操作 */}
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'flex-end', flexShrink: 0 }}>
                                        <button
                                            className={`btn btn-sm ${a.is_enabled ? 'btn-danger' : ''}`}
                                            onClick={() => toggleEnable(a)}
                                            disabled={toggling === a.id}
                                        >
                                            {a.is_enabled ? t.agents.disable : t.agents.enable}
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
        </div>
    )
}
