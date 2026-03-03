import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiGet } from '../api/client'
import { fmtTime, shortId, statusClass } from '../lib/format'

type TaskRead = {
  id: string
  title: string
  status: string
  created_at: number
  updated_at: number
}

export function Tasks() {
  const [tasks, setTasks] = useState<TaskRead[]>([])
  const [err, setErr] = useState<string>('')
  const [q, setQ] = useState('')

  useEffect(() => {
    apiGet<TaskRead[]>('/api/v0.1/tasks')
      .then(setTasks)
      .catch((e) => setErr(String(e)))
  }, [])

  const filtered = useMemo(() => {
    const qq = q.trim().toLowerCase()
    if (!qq) return tasks
    return tasks.filter((t) => `${t.title} ${t.id} ${t.status}`.toLowerCase().includes(qq))
  }, [tasks, q])

  return (
    <div className="panel">
      <div className="h1" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
        <span>Tasks</span>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="search title/id/status"
          style={{
            width: 320,
            maxWidth: '60vw',
            padding: '8px 10px',
            borderRadius: 10,
            border: '1px solid var(--border)',
            outline: 'none',
          }}
        />
      </div>

      {err ? <div className="error">{err}</div> : null}

      <table className="table">
        <thead>
          <tr>
            <th style={{ width: '44%' }}>title</th>
            <th>status</th>
            <th>created</th>
            <th>id</th>
            <th style={{ width: 80 }} />
          </tr>
        </thead>
        <tbody>
          {filtered.map((t) => (
            <tr key={t.id}>
              <td>
                <div style={{ fontWeight: 600 }}>{t.title}</div>
                <div style={{ color: 'var(--muted)', fontSize: 12 }}>updated: {fmtTime(t.updated_at)}</div>
              </td>
              <td>
                <span className={`badge ${statusClass(t.status)}`}>{t.status}</span>
              </td>
              <td style={{ color: 'var(--muted)' }}>{fmtTime(t.created_at)}</td>
              <td style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--muted)' }}>{shortId(t.id, 10)}</td>
              <td>
                <Link to={`/tasks/${t.id}`}>open</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div style={{ marginTop: 10, color: 'var(--muted)', fontSize: 12 }}>count: {filtered.length}</div>
    </div>
  )
}
