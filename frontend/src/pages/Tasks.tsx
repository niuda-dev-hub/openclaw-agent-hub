/**
 * Tasks - 任务列表页面
 * 支持搜索/状态过滤、创建任务弹窗。
 */
import { useEffect, useMemo, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { apiGet } from '../api/client'
import { fmtTime, shortId, statusClass } from '../lib/format'
import { useI18n } from '../i18n'
import { CreateTaskModal } from '../components/CreateTaskModal'

type TaskRead = {
  id: string
  title: string
  status: string
  created_at: number
  updated_at: number
}

const STATUS_FILTERS = ['all', 'draft', 'open', 'running', 'finalized', 'cancelled']

export function Tasks() {
  const { t } = useI18n()
  const [tasks, setTasks] = useState<TaskRead[]>([])
  const [err, setErr] = useState('')
  const [q, setQ] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [showCreate, setShowCreate] = useState(false)

  const load = useCallback(() => {
    apiGet<TaskRead[]>('/api/v0.1/tasks')
      .then(setTasks)
      .catch((e) => setErr(String(e)))
  }, [])

  useEffect(() => { load() }, [load])

  const filtered = useMemo(() => {
    let list = tasks
    if (statusFilter !== 'all') list = list.filter((t) => t.status === statusFilter)
    const qq = q.trim().toLowerCase()
    if (qq) list = list.filter((t) => `${t.title} ${t.id} ${t.status}`.toLowerCase().includes(qq))
    return list
  }, [tasks, q, statusFilter])

  return (
    <div style={{ display: 'grid', gap: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <div className="h1" style={{ margin: 0 }}>{t.tasks.title}</div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <input
            className="search-input"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={t.tasks.searchPlaceholder}
          />
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
            + {t.tasks.createTask}
          </button>
        </div>
      </div>

      {/* 状态过滤 tabs */}
      <div className="tabs">
        {STATUS_FILTERS.map((s) => (
          <button
            key={s}
            className={`tab-btn${statusFilter === s ? ' active' : ''}`}
            onClick={() => setStatusFilter(s)}
          >
            {s === 'all' ? '全部' : s}
          </button>
        ))}
      </div>

      {err && <div className="error">{err}</div>}

      <div className="panel" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="table">
          <thead>
            <tr>
              <th style={{ width: '44%', paddingLeft: 16 }}>{t.tasks.colTitle}</th>
              <th>{t.tasks.colStatus}</th>
              <th>{t.tasks.colCreated}</th>
              <th>{t.tasks.colId}</th>
              <th style={{ width: 60 }} />
            </tr>
          </thead>
          <tbody>
            {filtered.map((task) => (
              <tr key={task.id}>
                <td style={{ paddingLeft: 16 }}>
                  <div style={{ fontWeight: 600 }}>{task.title}</div>
                  <div style={{ color: 'var(--muted)', fontSize: 11 }}>
                    {t.tasks.updated}{fmtTime(task.updated_at)}
                  </div>
                </td>
                <td>
                  <span className={`badge ${statusClass(task.status)}`}>{task.status}</span>
                </td>
                <td style={{ color: 'var(--muted)', fontSize: 12 }}>{fmtTime(task.created_at)}</td>
                <td style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--muted)' }}>
                  {shortId(task.id, 10)}
                </td>
                <td style={{ paddingRight: 16 }}>
                  <Link to={`/tasks/${task.id}`}>{t.tasks.open}</Link>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', color: 'var(--muted)', padding: '24px 0' }}>
                  {t.common.noData}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="hint">共 {filtered.length} 条</div>

      {/* 创建任务弹窗 */}
      <CreateTaskModal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        onSuccess={() => load()}
      />
    </div>
  )
}
