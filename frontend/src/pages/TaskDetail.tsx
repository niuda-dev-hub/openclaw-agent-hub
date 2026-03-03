import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { apiGet } from '../api/client'
import { fmtTime, shortId, statusClass } from '../lib/format'

type TaskRead = {
  id: string
  title: string
  prompt: string
  status: string
  created_at: number
  updated_at: number
  expected_output_type?: string
}

type SubmissionRead = Record<string, unknown>
type EvaluationRead = Record<string, unknown>
type DecisionRead = Record<string, unknown>

function JsonBlock({ value }: { value: unknown }) {
  return <pre>{JSON.stringify(value, null, 2)}</pre>
}

export function TaskDetail() {
  const { taskId } = useParams()

  const [task, setTask] = useState<TaskRead | null>(null)
  const [subs, setSubs] = useState<SubmissionRead[] | null>(null)
  const [evals, setEvals] = useState<EvaluationRead[] | null>(null)
  const [decision, setDecision] = useState<DecisionRead | null>(null)
  const [err, setErr] = useState<string>('')

  useEffect(() => {
    if (!taskId) return
    ;(async () => {
      try {
        const [t, s, e, d] = await Promise.all([
          apiGet<TaskRead>(`/api/v0.1/tasks/${taskId}`),
          apiGet<SubmissionRead[]>(`/api/v0.1/tasks/${taskId}/submissions`),
          apiGet<EvaluationRead[]>(`/api/v0.1/tasks/${taskId}/evaluations`),
          apiGet<DecisionRead>(`/api/v0.1/tasks/${taskId}/decision`),
        ])
        setTask(t)
        setSubs(s)
        setEvals(e)
        setDecision(d)
      } catch (e) {
        setErr(String(e))
      }
    })()
  }, [taskId])

  return (
    <div style={{ display: 'grid', gap: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <div className="h1" style={{ margin: 0 }}>
            Task Detail
          </div>
          <div style={{ color: 'var(--muted)', fontFamily: 'var(--mono)', fontSize: 12 }}>id: {taskId}</div>
        </div>
        <Link to="/tasks">← Back to Tasks</Link>
      </div>

      {err ? <div className="error">{err}</div> : null}

      <div className="panel">
        <div className="h1">Task</div>
        {task ? (
          <div className="kv">
            <div className="k">title</div>
            <div className="v">{task.title}</div>

            <div className="k">status</div>
            <div className="v">
              <span className={`badge ${statusClass(task.status)}`}>{task.status}</span>
            </div>

            <div className="k">created</div>
            <div className="v">{fmtTime(task.created_at)}</div>

            <div className="k">updated</div>
            <div className="v">{fmtTime(task.updated_at)}</div>

            <div className="k">expected_output_type</div>
            <div className="v">{task.expected_output_type ?? '-'}</div>

            <div className="k">id</div>
            <div className="v">{task.id}</div>

            <div className="k">prompt</div>
            <div className="v">{task.prompt}</div>
          </div>
        ) : (
          <div style={{ color: 'var(--muted)' }}>loading...</div>
        )}

        {task ? (
          <details style={{ marginTop: 12 }}>
            <summary>raw JSON</summary>
            <div style={{ marginTop: 8 }}>
              <JsonBlock value={task} />
            </div>
          </details>
        ) : null}
      </div>

      <div className="split">
        <div className="panel">
          <div className="h1">Submissions</div>
          <div style={{ color: 'var(--muted)', fontSize: 12, marginBottom: 8 }}>count: {subs ? subs.length : '-'}</div>
          {subs ? <JsonBlock value={subs} /> : <div style={{ color: 'var(--muted)' }}>loading...</div>}
        </div>

        <div className="panel">
          <div className="h1">Evaluations</div>
          <div style={{ color: 'var(--muted)', fontSize: 12, marginBottom: 8 }}>count: {evals ? evals.length : '-'}</div>
          {evals ? <JsonBlock value={evals} /> : <div style={{ color: 'var(--muted)' }}>loading...</div>}
        </div>
      </div>

      <div className="panel">
        <div className="h1">Decision</div>
        {decision ? <JsonBlock value={decision} /> : <div style={{ color: 'var(--muted)' }}>loading...</div>}
      </div>

      <div style={{ color: 'var(--muted)', fontSize: 12 }}>
        tip: IDs are shortened in list view (e.g. {shortId('1234567890abcdef', 8)}).
      </div>
    </div>
  )
}
