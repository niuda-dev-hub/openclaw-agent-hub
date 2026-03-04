/**
 * Dashboard - 仪表盘页面
 * 展示统计数据（任务总数、进行中、已完成、在线 Agent 数）和最近任务列表。
 */
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiGet } from '../api/client'
import { useI18n } from '../i18n'
import { fmtTime, statusClass } from '../lib/format'
import { calcOnlineStatus } from '../components/AgentStatusBadge'

interface TaskRead {
  id: string
  title: string
  status: string
  created_at: number
}

interface AgentRead {
  id: string
  last_heartbeat_at?: number | null
}

export function Dashboard() {
  const { t } = useI18n()
  const [tasks, setTasks] = useState<TaskRead[]>([])
  const [agents, setAgents] = useState<AgentRead[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      apiGet<TaskRead[]>('/api/v0.1/tasks').catch(() => [] as TaskRead[]),
      apiGet<AgentRead[]>('/api/v0.1/agents').catch(() => [] as AgentRead[]),
    ]).then(([t, a]) => {
      setTasks(t)
      setAgents(a)
      setLoading(false)
    })
  }, [])

  const running = tasks.filter((t) => t.status === 'running').length
  const finalized = tasks.filter((t) => t.status === 'finalized').length
  const onlineCount = agents.filter((a) => calcOnlineStatus(a.last_heartbeat_at) !== 'offline').length

  const recent = tasks.slice(0, 8)

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <div className="h1" style={{ margin: 0 }}>{t.dashboard.title}</div>

      {/* 统计卡片 */}
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-label">{t.dashboard.totalTasks}</div>
          <div className="stat-value">{loading ? '-' : tasks.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">{t.dashboard.runningTasks}</div>
          <div className="stat-value" style={{ color: 'var(--warn)' }}>{loading ? '-' : running}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">{t.dashboard.finalizedTasks}</div>
          <div className="stat-value" style={{ color: 'var(--ok)' }}>{loading ? '-' : finalized}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">{t.dashboard.onlineAgents}</div>
          <div className="stat-value" style={{ color: 'var(--brand)' }}>{loading ? '-' : onlineCount}</div>
        </div>
      </div>

      {/* 最近任务 */}
      <div className="panel">
        <div className="panel-header">
          <div className="h2" style={{ margin: 0 }}>{t.dashboard.recentTasks}</div>
          <Link to="/tasks">{t.tasks.title} →</Link>
        </div>
        {loading
          ? <div style={{ color: 'var(--muted)' }}>{t.common.loading}</div>
          : recent.length === 0
            ? <div style={{ color: 'var(--muted)' }}>{t.common.noData}</div>
            : (
              <table className="table">
                <thead>
                  <tr>
                    <th style={{ width: '50%' }}>{t.tasks.colTitle}</th>
                    <th>{t.tasks.colStatus}</th>
                    <th>{t.tasks.colCreated}</th>
                    <th style={{ width: 60 }} />
                  </tr>
                </thead>
                <tbody>
                  {recent.map((task) => (
                    <tr key={task.id}>
                      <td style={{ fontWeight: 500 }}>{task.title}</td>
                      <td>
                        <span className={`badge ${statusClass(task.status)}`}>{task.status}</span>
                      </td>
                      <td style={{ color: 'var(--muted)', fontSize: 12 }}>{fmtTime(task.created_at)}</td>
                      <td>
                        <Link to={`/tasks/${task.id}`}>{t.tasks.open}</Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
      </div>
    </div>
  )
}
