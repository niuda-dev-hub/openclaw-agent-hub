import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { apiGet } from '../api/client'

type TaskRead = {
  id: string
  title: string
  prompt: string
  status: string
  created_at: number
  updated_at: number
}

type SubmissionRead = Record<string, unknown>
type EvaluationRead = Record<string, unknown>
type DecisionRead = Record<string, unknown>

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
    <div style={{ padding: 16 }}>
      <h2>Task Detail</h2>
      {err ? <pre style={{ color: 'crimson' }}>{err}</pre> : null}

      <section style={{ marginTop: 12 }}>
        <h3>Task</h3>
        {task ? (
          <pre style={{ background: '#fafafa', padding: 12, overflow: 'auto' }}>{JSON.stringify(task, null, 2)}</pre>
        ) : (
          <p>loading...</p>
        )}
      </section>

      <section style={{ marginTop: 12 }}>
        <h3>Submissions</h3>
        {subs ? (
          <pre style={{ background: '#fafafa', padding: 12, overflow: 'auto' }}>{JSON.stringify(subs, null, 2)}</pre>
        ) : (
          <p>loading...</p>
        )}
      </section>

      <section style={{ marginTop: 12 }}>
        <h3>Evaluations</h3>
        {evals ? (
          <pre style={{ background: '#fafafa', padding: 12, overflow: 'auto' }}>{JSON.stringify(evals, null, 2)}</pre>
        ) : (
          <p>loading...</p>
        )}
      </section>

      <section style={{ marginTop: 12 }}>
        <h3>Decision</h3>
        {decision ? (
          <pre style={{ background: '#fafafa', padding: 12, overflow: 'auto' }}>{JSON.stringify(decision, null, 2)}</pre>
        ) : (
          <p>loading...</p>
        )}
      </section>
    </div>
  )
}
