/**
 * TaskDetail - 任务详情页面
 * 包含：任务信息、指派 Agent 按钮、参与者、提交产物、评分、终审决策、审计事件时间线。
 */
import { useEffect, useState, useCallback } from 'react'
import { Link, useParams } from 'react-router-dom'
import { apiGet } from '../api/client'
import { fmtTime, shortId, statusClass } from '../lib/format'
import { useI18n } from '../i18n'
import { AssignTaskModal } from '../components/AssignTaskModal'

interface TaskRead {
  id: string
  title: string
  prompt: string
  status: string
  expected_output_type?: string
  created_by?: string | null
  created_at: number
  updated_at: number
}

interface SubmissionRead {
  id: string
  run_id: string
  content_type: string
  content: string
  summary?: string | null
  created_at: number
}

interface EvaluationRead {
  id: string
  submission_id: string
  source: string
  total_score: number
  comments?: string | null
  created_at: number
}

interface EventRead {
  id: string
  event_type: string
  actor_type: string
  actor_id?: string | null
  created_at: number
}

interface DecisionRead {
  id: string
  winner_submission_id: string
  rationale?: string | null
  decided_by?: string | null
  created_at: number
}

/** 安全 JSON parse，失败返回 null */
function safeParse(s: unknown) {
  try { return JSON.parse(String(s)) } catch { return null }
}

export function TaskDetail() {
  const { taskId } = useParams<{ taskId: string }>()
  const { t } = useI18n()

  const [task, setTask] = useState<TaskRead | null>(null)
  const [subs, setSubs] = useState<SubmissionRead[]>([])
  const [evals, setEvals] = useState<EvaluationRead[]>([])
  const [decision, setDecision] = useState<DecisionRead | null>(null)
  const [events, setEvents] = useState<EventRead[]>([])
  const [err, setErr] = useState('')
  const [showAssign, setShowAssign] = useState(false)
  const [activeTab, setActiveTab] = useState<'subs' | 'evals' | 'events'>('subs')

  const load = useCallback(async () => {
    if (!taskId) return
    setErr('')
    try {
      const [taskRes, subsRes, evalsRes, decRes, eventsRes] = await Promise.allSettled([
        apiGet<TaskRead>(`/api/v0.1/tasks/${taskId}`),
        apiGet<SubmissionRead[]>(`/api/v0.1/tasks/${taskId}/submissions`),
        apiGet<EvaluationRead[]>(`/api/v0.1/tasks/${taskId}/evaluations`),
        apiGet<DecisionRead>(`/api/v0.1/tasks/${taskId}/decision`),
        apiGet<EventRead[]>(`/api/v0.1/tasks/${taskId}/events`),
      ])
      if (taskRes.status === 'fulfilled') setTask(taskRes.value)
      else setErr(String(taskRes.reason))
      if (subsRes.status === 'fulfilled') setSubs(subsRes.value)
      if (evalsRes.status === 'fulfilled') setEvals(evalsRes.value)
      if (decRes.status === 'fulfilled') setDecision(decRes.value)
      // 404 是正常的，decision 不存在时
      if (eventsRes.status === 'fulfilled') setEvents(eventsRes.value)
    } catch (e) {
      setErr(String(e))
    }
  }, [taskId])

  useEffect(() => { load() }, [load])

  const evalMap = new Map<string, EvaluationRead[]>()
  evals.forEach((ev) => {
    const list = evalMap.get(ev.submission_id) ?? []
    list.push(ev)
    evalMap.set(ev.submission_id, list)
  })

  return (
    <div style={{ display: 'grid', gap: 12 }}>
      {/* 标题行 */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
        <div>
          <div className="h1" style={{ margin: 0 }}>{task?.title ?? t.taskDetail.title}</div>
          <div style={{ color: 'var(--muted)', fontFamily: 'var(--mono)', fontSize: 11 }}>
            {taskId}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button className="btn btn-primary" onClick={() => setShowAssign(true)}>
            ⚡ {t.taskDetail.assignAgent}
          </button>
          <Link to="/tasks" className="btn">{t.common.back}</Link>
        </div>
      </div>

      {err && <div className="error">{err}</div>}

      {/* 任务基础信息 */}
      <div className="panel">
        {task ? (
          <div className="kv">
            <div className="k">{t.tasks.colStatus}</div>
            <div className="v">
              <span className={`badge ${statusClass(task.status)}`}>{task.status}</span>
            </div>
            <div className="k">{t.tasks.colCreated}</div>
            <div className="v">{fmtTime(task.created_at)}</div>
            <div className="k">updated</div>
            <div className="v">{fmtTime(task.updated_at)}</div>
            <div className="k">expected_output_type</div>
            <div className="v">{task.expected_output_type ?? '-'}</div>
            <div className="k">created_by</div>
            <div className="v">{task.created_by ?? '-'}</div>
            <div className="k">{t.taskDetail.promptLabel}</div>
            <div className="v">{task.prompt}</div>
          </div>
        ) : (
          <div style={{ color: 'var(--muted)' }}>{t.common.loading}</div>
        )}
      </div>

      {/* 标签页 */}
      <div className="panel" style={{ padding: 0 }}>
        <div className="tabs" style={{ margin: 0, padding: '0 12px' }}>
          <button
            className={`tab-btn${activeTab === 'subs' ? ' active' : ''}`}
            onClick={() => setActiveTab('subs')}
          >
            {t.taskDetail.submissions} ({subs.length})
          </button>
          <button
            className={`tab-btn${activeTab === 'evals' ? ' active' : ''}`}
            onClick={() => setActiveTab('evals')}
          >
            {t.taskDetail.evaluations} ({evals.length})
          </button>
          <button
            className={`tab-btn${activeTab === 'events' ? ' active' : ''}`}
            onClick={() => setActiveTab('events')}
          >
            {t.taskDetail.events} ({events.length})
          </button>
        </div>

        <div style={{ padding: 12 }}>
          {/* 提交产物 */}
          {activeTab === 'subs' && (
            subs.length === 0
              ? <div style={{ color: 'var(--muted)' }}>{t.taskDetail.noSubmissions}</div>
              : (
                <div style={{ display: 'grid', gap: 10 }}>
                  {subs.map((s) => (
                    <div key={s.id} className="panel" style={{ boxShadow: 'none', padding: 12 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                        <div>
                          <span className="badge info">{s.content_type}</span>
                          {s.summary && <span style={{ marginLeft: 8, fontSize: 12 }}>{s.summary}</span>}
                        </div>
                        <div style={{ color: 'var(--muted)', fontSize: 11 }}>{fmtTime(s.created_at)}</div>
                      </div>
                      <pre style={{ maxHeight: 200, overflowY: 'auto' }}>{s.content}</pre>
                      <div style={{ marginTop: 6, color: 'var(--muted)', fontSize: 11 }}>
                        run: {shortId(s.run_id)} | sub: {shortId(s.id)}
                      </div>
                    </div>
                  ))}
                </div>
              )
          )}

          {/* 评分 */}
          {activeTab === 'evals' && (
            evals.length === 0
              ? <div style={{ color: 'var(--muted)' }}>{t.taskDetail.noEvaluations}</div>
              : (
                <table className="table">
                  <thead>
                    <tr>
                      <th>submission</th>
                      <th>source</th>
                      <th>score</th>
                      <th>comments</th>
                      <th>time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evals.map((ev) => (
                      <tr key={ev.id}>
                        <td style={{ fontFamily: 'var(--mono)', fontSize: 11 }}>{shortId(ev.submission_id)}</td>
                        <td><span className="badge">{ev.source}</span></td>
                        <td style={{ fontWeight: 700, color: 'var(--brand)' }}>{ev.total_score}</td>
                        <td style={{ color: 'var(--muted)', fontSize: 12 }}>{ev.comments ?? '-'}</td>
                        <td style={{ color: 'var(--muted)', fontSize: 11 }}>{fmtTime(ev.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )
          )}

          {/* 事件时间线 */}
          {activeTab === 'events' && (
            events.length === 0
              ? <div style={{ color: 'var(--muted)' }}>{t.taskDetail.noEvents}</div>
              : (
                <ul className="timeline">
                  {events.map((ev) => (
                    <li key={ev.id} className="timeline-item">
                      <span className="timeline-time">{fmtTime(ev.created_at)}</span>
                      <span className="timeline-type">{ev.event_type}</span>
                      <span className="timeline-actor">{ev.actor_type}{ev.actor_id ? `:${shortId(ev.actor_id)}` : ''}</span>
                    </li>
                  ))}
                </ul>
              )
          )}
        </div>
      </div>

      {/* 终审决策 */}
      {decision && (
        <div className="panel">
          <div className="h2">{t.taskDetail.decision}</div>
          <div className="kv">
            <div className="k">winner</div>
            <div className="v">{shortId(decision.winner_submission_id)}</div>
            <div className="k">decided_by</div>
            <div className="v">{decision.decided_by ?? '-'}</div>
            <div className="k">rationale</div>
            <div className="v">{decision.rationale ?? '-'}</div>
            <div className="k">time</div>
            <div className="v">{fmtTime(decision.created_at)}</div>
          </div>
        </div>
      )}

      {/* 指派 Agent 弹窗 */}
      {taskId && (
        <AssignTaskModal
          open={showAssign}
          onClose={() => setShowAssign(false)}
          taskId={taskId}
          onSuccess={() => load()}
        />
      )}
    </div>
  )
}
