/**
 * AssignTaskModal - 指派 Agent 执行任务的弹窗
 * 支持多选 Agent，调用 POST /tasks/{task_id}/start
 */
import { useEffect, useState } from 'react'
import { Modal } from './Modal'
import { AgentStatusBadge } from './AgentStatusBadge'
import { apiGet, apiPost } from '../api/client'
import { useI18n } from '../i18n'

interface Agent {
    id: string
    name: string
    agent_type: string
    is_enabled: boolean
    last_heartbeat_at?: number | null
}

interface AssignTaskModalProps {
    open: boolean
    onClose: () => void
    taskId: string
    /** 成功后回调 */
    onSuccess?: () => void
}

export function AssignTaskModal({ open, onClose, taskId, onSuccess }: AssignTaskModalProps) {
    const { t } = useI18n()
    const [agents, setAgents] = useState<Agent[]>([])
    const [selected, setSelected] = useState<Set<string>>(new Set())
    const [loading, setLoading] = useState(false)
    const [submitting, setSubmitting] = useState(false)
    const [err, setErr] = useState('')

    // 加载 Agent 列表
    useEffect(() => {
        if (!open) return
        setLoading(true)
        setErr('')
        apiGet<Agent[]>('/api/v0.1/agents')
            .then((list) => setAgents(list.filter((a) => a.is_enabled)))
            .catch((e) => setErr(String(e)))
            .finally(() => setLoading(false))
    }, [open])

    const toggle = (id: string) => {
        setSelected((prev) => {
            const next = new Set(prev)
            if (next.has(id)) next.delete(id)
            else next.add(id)
            return next
        })
    }

    const handleAssign = async () => {
        if (selected.size === 0) return
        setSubmitting(true)
        setErr('')
        try {
            await apiPost(`/api/v0.1/tasks/${taskId}/start`, {
                agent_ids: Array.from(selected),
                run_params: {},
            })
            onSuccess?.()
            onClose()
        } catch (e) {
            setErr(String(e))
        } finally {
            setSubmitting(false)
        }
    }

    const footer = (
        <>
            <button className="btn" onClick={onClose} disabled={submitting}>{t.common.cancel}</button>
            <button
                className="btn btn-primary"
                onClick={handleAssign}
                disabled={selected.size === 0 || submitting}
            >
                {submitting ? t.common.loading : t.common.assign}
            </button>
        </>
    )

    return (
        <Modal open={open} onClose={onClose} title={t.assignTask.title} footer={footer}>
            {err && <div className="error" style={{ marginBottom: 10 }}>{err}</div>}
            {loading && <div style={{ color: 'var(--muted)' }}>{t.common.loading}</div>}
            {!loading && agents.length === 0 && (
                <div style={{ color: 'var(--muted)' }}>{t.assignTask.noAgentsAvailable}</div>
            )}
            <ul className="agent-select-list">
                {agents.map((a) => (
                    <li
                        key={a.id}
                        className={`agent-select-item${selected.has(a.id) ? ' selected' : ''}`}
                        onClick={() => toggle(a.id)}
                    >
                        <input
                            type="checkbox"
                            checked={selected.has(a.id)}
                            onChange={() => toggle(a.id)}
                            onClick={(e) => e.stopPropagation()}
                        />
                        <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ fontWeight: 600, fontSize: 13 }}>{a.name}</div>
                            <div style={{ color: 'var(--muted)', fontSize: 12 }}>{a.agent_type}</div>
                        </div>
                        <AgentStatusBadge lastHeartbeatAt={a.last_heartbeat_at} />
                    </li>
                ))}
            </ul>
            {selected.size > 0 && (
                <div className="hint">{t.assignTask.selectAgent}: {selected.size} 个</div>
            )}
        </Modal>
    )
}
