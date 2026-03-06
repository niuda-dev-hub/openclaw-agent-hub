/**
 * Admin.tsx - Admin UI 管理后台页面（Issue #28）
 * 提供任务/运行/提交/评审/决策的统一管理视图。
 * 管理员可查看所有状态的任务并进行内容终审操作。
 */
import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { apiGet, apiPost } from '../api/client'
import { useI18n } from '../i18n'
import { shortId, timeAgo } from '../lib/format'

interface TaskRead {
    id: string
    title: string
    status: string
    created_by: string | null
    created_at: number
    project_id: string | null
}

interface RunRead {
    id: string
    task_id: string
    status: string
    created_at: number
    error_message: string | null
}

interface SubmissionRead {
    id: string
    task_id: string
    agent_id: string
    content: string
    created_at: number
}

type TabKey = 'tasks' | 'runs' | 'submissions'

export function Admin() {
    const { t } = useI18n()
    const [tab, setTab] = useState<TabKey>('tasks')
    const [tasks, setTasks] = useState<TaskRead[]>([])
    const [runs, setRuns] = useState<RunRead[]>([])
    const [submissions, setSubmissions] = useState<SubmissionRead[]>([])
    const [loading, setLoading] = useState(false)
    const [err, setErr] = useState('')
    const [actionMsg, setActionMsg] = useState('')

    // 搜索过滤
    const [query, setQuery] = useState('')

    const load = useCallback(() => {
        setLoading(true)
        setErr('')
        Promise.all([
            apiGet<TaskRead[]>('/api/v0.1/tasks'),
            apiGet<RunRead[]>('/api/v0.1/runs').catch(() => [] as RunRead[]),
            apiGet<SubmissionRead[]>('/api/v0.1/submissions').catch(() => [] as SubmissionRead[]),
        ])
            .then(([t, r, s]) => {
                setTasks(t)
                setRuns(r)
                setSubmissions(s)
                setLoading(false)
            })
            .catch((e) => { setErr(String(e)); setLoading(false) })
    }, [])

    useEffect(() => { load() }, [load])

    // 操作：Finalize 任务
    async function finalizeTask(taskId: string) {
        try {
            await apiPost(`/api/v0.1/tasks/${taskId}/finalize`, {})
            setActionMsg(`✅ 任务 ${shortId(taskId)} 已 Finalize`)
            load()
        } catch (e) {
            setActionMsg(`❌ 失败: ${e}`)
        }
    }

    // 搜索过滤逻辑
    const q = query.toLowerCase()
    const filteredTasks = tasks.filter(t =>
        !q || t.title.toLowerCase().includes(q) || t.id.includes(q) || t.status.includes(q)
    )
    const filteredRuns = runs.filter(r =>
        !q || r.id.includes(q) || r.task_id.includes(q) || r.status.includes(q)
    )
    const filteredSubs = submissions.filter(s =>
        !q || s.id.includes(q) || s.task_id.includes(q) || s.agent_id.includes(q)
    )

    const tabBtnStyle = (active: boolean) => ({
        padding: '6px 18px',
        borderRadius: 6,
        border: 'none',
        cursor: 'pointer',
        fontWeight: active ? 700 : 400,
        background: active ? 'var(--accent)' : 'var(--surface)',
        color: active ? '#fff' : 'var(--text)',
        transition: 'all 0.15s',
    })

    return (
        <div style={{ display: 'grid', gap: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
                <div className="h1" style={{ margin: 0 }}>{t.admin.title}</div>
                <button className="btn btn-sm" onClick={load}>{t.common.refresh}</button>
            </div>

            {err && <div className="error">{err}</div>}
            {actionMsg && (
                <div className="panel" style={{ padding: '8px 16px', background: 'var(--surface)', borderLeft: '3px solid var(--accent)' }}>
                    {actionMsg}
                    <button className="btn btn-sm" style={{ marginLeft: 12 }} onClick={() => setActionMsg('')}>✕</button>
                </div>
            )}

            {/* 搜索框 */}
            <input
                className="input"
                placeholder={t.common.search + ' ID / 标题 / 状态...'}
                value={query}
                onChange={e => setQuery(e.target.value)}
                style={{ maxWidth: 360 }}
            />

            {/* Tab 切换 */}
            <div style={{ display: 'flex', gap: 8 }}>
                {(['tasks', 'runs', 'submissions'] as TabKey[]).map(k => (
                    <button key={k} style={tabBtnStyle(tab === k)} onClick={() => setTab(k)}>
                        {t.admin[k]}
                        <span style={{ marginLeft: 6, fontSize: 11, opacity: 0.7 }}>
                            ({k === 'tasks' ? filteredTasks.length : k === 'runs' ? filteredRuns.length : filteredSubs.length})
                        </span>
                    </button>
                ))}
            </div>

            {loading && <div style={{ color: 'var(--muted)' }}>{t.common.loading}</div>}

            {/* ─── 任务列表 ─── */}
            {!loading && tab === 'tasks' && (
                <div className="panel" style={{ padding: 0, overflow: 'hidden' }}>
                    <table className="table">
                        <thead>
                            <tr>
                                <th style={{ paddingLeft: 16 }}>ID</th>
                                <th>{t.admin.colTitle}</th>
                                <th>{t.admin.colStatus}</th>
                                <th>{t.admin.colCreated}</th>
                                <th>{t.admin.colActions}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredTasks.length === 0 ? (
                                <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--muted)', padding: 24 }}>{t.common.noData}</td></tr>
                            ) : filteredTasks.map(task => (
                                <tr key={task.id}>
                                    <td style={{ paddingLeft: 16, fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--muted)' }}>
                                        {shortId(task.id)}
                                    </td>
                                    <td>
                                        <Link to={`/tasks/${task.id}`} style={{ color: 'var(--accent)', textDecoration: 'none' }}>
                                            {task.title}
                                        </Link>
                                    </td>
                                    <td>
                                        <span className={`badge badge-${task.status}`}>{task.status}</span>
                                    </td>
                                    <td style={{ color: 'var(--muted)', fontSize: 12 }}>{timeAgo(task.created_at)}</td>
                                    <td>
                                        <div style={{ display: 'flex', gap: 6 }}>
                                            {task.status === 'running' && (
                                                <button className="btn btn-sm" onClick={() => finalizeTask(task.id)}>
                                                    {t.admin.finalize}
                                                </button>
                                            )}
                                            <Link to={`/tasks/${task.id}`}>
                                                <button className="btn btn-sm">{t.common.back === '返回' ? '查看' : 'View'}</button>
                                            </Link>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* ─── Run 列表 ─── */}
            {!loading && tab === 'runs' && (
                <div className="panel" style={{ padding: 0, overflow: 'hidden' }}>
                    <table className="table">
                        <thead>
                            <tr>
                                <th style={{ paddingLeft: 16 }}>Run ID</th>
                                <th>Task ID</th>
                                <th>{t.admin.colStatus}</th>
                                <th>{t.admin.colCreated}</th>
                                <th>Error</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredRuns.length === 0 ? (
                                <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--muted)', padding: 24 }}>{t.common.noData}</td></tr>
                            ) : filteredRuns.map(run => (
                                <tr key={run.id}>
                                    <td style={{ paddingLeft: 16, fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--muted)' }}>
                                        {shortId(run.id)}
                                    </td>
                                    <td style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--muted)' }}>
                                        <Link to={`/tasks/${run.task_id}`} style={{ color: 'var(--accent)', textDecoration: 'none' }}>
                                            {shortId(run.task_id)}
                                        </Link>
                                    </td>
                                    <td><span className={`badge badge-${run.status}`}>{run.status}</span></td>
                                    <td style={{ color: 'var(--muted)', fontSize: 12 }}>{timeAgo(run.created_at)}</td>
                                    <td style={{ color: 'var(--error)', fontSize: 12, maxWidth: 240, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                        {run.error_message || '—'}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* ─── 提交列表 ─── */}
            {!loading && tab === 'submissions' && (
                <div className="panel" style={{ padding: 0, overflow: 'hidden' }}>
                    <table className="table">
                        <thead>
                            <tr>
                                <th style={{ paddingLeft: 16 }}>Submission ID</th>
                                <th>Task</th>
                                <th>Agent</th>
                                <th>{t.admin.colCreated}</th>
                                <th>Content 预览</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredSubs.length === 0 ? (
                                <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--muted)', padding: 24 }}>{t.common.noData}</td></tr>
                            ) : filteredSubs.map(sub => (
                                <tr key={sub.id}>
                                    <td style={{ paddingLeft: 16, fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--muted)' }}>
                                        {shortId(sub.id)}
                                    </td>
                                    <td>
                                        <Link to={`/tasks/${sub.task_id}`} style={{ color: 'var(--accent)', textDecoration: 'none' }}>
                                            {shortId(sub.task_id)}
                                        </Link>
                                    </td>
                                    <td style={{ fontFamily: 'var(--mono)', fontSize: 11 }}>{shortId(sub.agent_id)}</td>
                                    <td style={{ color: 'var(--muted)', fontSize: 12 }}>{timeAgo(sub.created_at)}</td>
                                    <td style={{ maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 12 }}>
                                        {sub.content}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    )
}
