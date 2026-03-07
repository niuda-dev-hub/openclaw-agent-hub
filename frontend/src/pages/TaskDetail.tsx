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
  reward_usd: number   // 奖励金额（USD）原字段 total_score
  comments?: string | null
  created_at: number
}

interface EventRead {
  id: string
  event_type: string
  actor_type: string
  actor_id?: string | null
  payload?: unknown
  created_at: number
}

interface DecisionRead {
  id: string
  winner_submission_id: string
  rationale?: string | null
  decided_by?: string | null
  created_at: number
}

interface RunRead {
  id: string
  task_id: string
  agent_id: string
  status: string
  started_at?: number | null
  finished_at?: number | null
}

interface DevTaskRead {
  id: string
  run_id: string
  title: string
  description?: string | null
  priority: number
  status: string
  created_at: number
  updated_at: number
}

interface DevTaskProgress {
  run_id: string
  total: number
  done: number
  in_progress: number
  pending: number
  failed: number
  progress_pct: number
}

/** 安全 JSON parse，失败返回 null */
function safeParse(s: unknown) {
  try { return JSON.parse(String(s)) } catch { return null }
}

export function TaskDetail() {
  const { taskId } = useParams<{ taskId: string }>()
  const { t } = useI18n()

  const [task, setTask] = useState<TaskRead | null>(null)
  const [runs, setRuns] = useState<RunRead[]>([])
  const [devTasksMap, setDevTasksMap] = useState<Record<string, DevTaskRead[]>>({})
  const [progressMap, setProgressMap] = useState<Record<string, DevTaskProgress>>({})
  const [subs, setSubs] = useState<SubmissionRead[]>([])
  const [evals, setEvals] = useState<EvaluationRead[]>([])
  const [decision, setDecision] = useState<DecisionRead | null>(null)
  const [events, setEvents] = useState<EventRead[]>([])
  const [err, setErr] = useState('')
  const [showAssign, setShowAssign] = useState(false)
  const [activeTab, setActiveTab] = useState<'runs' | 'subs' | 'evals' | 'events'>('runs')

  const load = useCallback(async () => {
    if (!taskId) return
    setErr('')
    try {
      const [taskRes, runsRes, subsRes, evalsRes, decRes, eventsRes] = await Promise.allSettled([
        apiGet<TaskRead>(`/api/v0.1/tasks/${taskId}`),
        apiGet<RunRead[]>(`/api/v0.1/tasks/${taskId}/runs`),
        apiGet<SubmissionRead[]>(`/api/v0.1/tasks/${taskId}/submissions`),
        apiGet<EvaluationRead[]>(`/api/v0.1/tasks/${taskId}/evaluations`),
        apiGet<DecisionRead>(`/api/v0.1/tasks/${taskId}/decision`),
        apiGet<EventRead[]>(`/api/v0.1/tasks/${taskId}/events`),
      ])
      if (taskRes.status === 'fulfilled') setTask(taskRes.value)
      else setErr(String(taskRes.reason))
      
      // 加载 runs
      if (runsRes.status === 'fulfilled') {
        const runsData = runsRes.value
        setRuns(runsData)
        
        // 加载每个 run 的 dev-tasks 和进度
        const devTasksResult: Record<string, DevTaskRead[]> = {}
        const progressResult: Record<string, DevTaskProgress> = {}
        
        for (const run of runsData) {
          try {
            const [devTasks, progress] = await Promise.all([
              apiGet<DevTaskRead[]>(`/api/v0.1/runs/${run.id}/dev-tasks`),
              apiGet<DevTaskProgress>(`/api/v0.1/runs/${run.id}/dev-tasks/progress`),
            ])
            devTasksResult[run.id] = devTasks
            progressResult[run.id] = progress
          } catch {
            devTasksResult[run.id] = []
            progressResult[run.id] = { run_id: run.id, total: 0, done: 0, in_progress: 0, pending: 0, failed: 0, progress_pct: 0 }
          }
        }
        
        setDevTasksMap(devTasksResult)
        setProgressMap(progressResult)
      }
      
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
            className={`tab-btn${activeTab === 'runs' ? ' active' : ''}`}
            onClick={() => setActiveTab('runs')}
          >
            开发进度 ({runs.length})
          </button>
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
          {/* 开发进度 - Runs */}
          {activeTab === 'runs' && (
            runs.length === 0
              ? <div style={{ color: 'var(--muted)' }}>暂无参与 Agent</div>
              : (
                <div style={{ display: 'grid', gap: 12 }}>
                  {runs.map((run) => {
                    const devTasks = devTasksMap[run.id] || []
                    const progress = progressMap[run.id]
                    return (
                      <div key={run.id} className="panel" style={{ boxShadow: 'none', padding: 12 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                          <div>
                            <span className="badge info">Agent: {shortId(run.agent_id)}</span>
                            <span className={`badge ${statusClass(run.status)}`} style={{ marginLeft: 8 }}>{run.status}</span>
                          </div>
                          {progress && progress.total > 0 && (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                              <div style={{ width: 100, height: 6, background: 'var(--bg)', borderRadius: 3, overflow: 'hidden' }}>
                                <div style={{ width: `${progress.progress_pct}%`, height: '100%', background: progress.progress_pct === 100 ? 'var(--ok)' : 'var(--accent)', transition: 'width 0.3s' }} />
                              </div>
                              <span style={{ fontSize: 12, color: 'var(--muted)' }}>{progress.progress_pct}%</span>
                            </div>
                          )}
                        </div>
                        
                        {/* 开发子任务列表 */}
                        {devTasks.length > 0 && (
                          <div style={{ marginTop: 8 }}>
                            <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 4 }}>开发子任务:</div>
                            <div style={{ display: 'grid', gap: 4 }}>
                              {devTasks.map((dt) => (
                                <div key={dt.id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
                                  <span className={`badge ${dt.status === 'done' ? 'ok' : dt.status === 'failed' ? 'error' : dt.status === 'in_progress' ? 'warn' : ''}`}>
                                    {dt.status === 'done' ? '✓' : dt.status === 'failed' ? '✗' : dt.status === 'in_progress' ? '→' : '○'}
                                  </span>
                                  <span style={{ flex: 1 }}>{dt.title}</span>
                                  <span style={{ color: 'var(--muted)', fontSize: 10 }}>{fmtTime(dt.updated_at)}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {progress && (
                          <div style={{ marginTop: 8, fontSize: 11, color: 'var(--muted)' }}>
                            进度: {progress.done}/{progress.total} 完成, {progress.in_progress} 进行中, {progress.pending} 待处理
                            {progress.failed > 0 && <span style={{ color: 'var(--error)', marginLeft: 8 }}>• {progress.failed} 失败</span>}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )
          )}
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
                      <th>💰 reward (USD)</th>
                      <th>comments</th>
                      <th>time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evals.map((ev) => (
                      <tr key={ev.id}>
                        <td style={{ fontFamily: 'var(--mono)', fontSize: 11 }}>{shortId(ev.submission_id)}</td>
                        <td><span className="badge">{ev.source}</span></td>
                        <td style={{ fontWeight: 700, color: 'var(--ok)' }}>${ev.reward_usd.toFixed(4)}</td>
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
                  {events.map((ev) => {
                    const payloadObj = safeParse(ev.payload)
                    const payloadText = payloadObj ? JSON.stringify(payloadObj, null, 2) : (ev.payload == null ? '' : String(ev.payload))
                    return (
                      <li key={ev.id} className="timeline-item" style={{ alignItems: 'start' }}>
                        <span className="timeline-time">{fmtTime(ev.created_at)}</span>
                        <span className="timeline-type">{ev.event_type}</span>
                        <span className="timeline-actor">{ev.actor_type}{ev.actor_id ? `:${shortId(ev.actor_id)}` : ''}</span>
                        {payloadText && (
                          <pre style={{ gridColumn: '1 / -1', margin: '6px 0 0 0', maxHeight: 160, overflowY: 'auto' }}>
                            {payloadText}
                          </pre>
                        )}
                      </li>
                    )
                  })}
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
