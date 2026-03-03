import { useEffect, useState } from 'react'
import { apiGet } from '../api/client'

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

  useEffect(() => {
    apiGet<TaskRead[]>('/api/v0.1/tasks')
      .then(setTasks)
      .catch((e) => setErr(String(e)))
  }, [])

  return (
    <div style={{ padding: 16 }}>
      <h2>Tasks</h2>
      {err ? <pre style={{ color: 'crimson' }}>{err}</pre> : null}
      <table cellPadding={8} style={{ borderCollapse: 'collapse', width: '100%' }}>
        <thead>
          <tr>
            <th align="left">title</th>
            <th align="left">status</th>
            <th align="left">id</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((t) => (
            <tr key={t.id} style={{ borderTop: '1px solid #eee' }}>
              <td>{t.title}</td>
              <td>{t.status}</td>
              <td style={{ fontFamily: 'monospace', fontSize: 12 }}>{t.id}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
