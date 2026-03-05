import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { apiGet } from '../api/client'
import { fmtTime, shortId } from '../lib/format'
import { AdminTakeoverProjectModal } from '../components/AdminTakeoverProjectModal'

interface ProjectRead {
  id: string
  title: string
  description?: string | null
  publisher_type: string
  publisher_id: string
  stake_points: number
  status: string
  created_at: number
  updated_at: number
}

export function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>()
  const [p, setP] = useState<ProjectRead | null>(null)
  const [err, setErr] = useState('')
  const [showTakeover, setShowTakeover] = useState(false)

  const load = useCallback(async () => {
    if (!projectId) return
    setErr('')
    try {
      const res = await apiGet<ProjectRead>(`/api/v0.1/projects/${projectId}`)
      setP(res)
    } catch (e) {
      setErr(String(e))
    }
  }, [projectId])

  useEffect(() => { load() }, [load])

  return (
    <div style={{ display: 'grid', gap: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
        <div>
          <div className="h1" style={{ margin: 0 }}>{p?.title ?? 'Project'}</div>
          <div style={{ color: 'var(--muted)', fontFamily: 'var(--mono)', fontSize: 11 }}>{projectId}</div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button className="btn btn-danger" onClick={() => setShowTakeover(true)} disabled={!projectId}>
            管理员接管
          </button>
          <Link to="/" className="btn">返回</Link>
        </div>
      </div>

      {err && <div className="error">{err}</div>}

      <div className="panel">
        {p ? (
          <div className="kv">
            <div className="k">status</div>
            <div className="v">{p.status}</div>
            <div className="k">publisher</div>
            <div className="v">{p.publisher_type}:{shortId(p.publisher_id)}</div>
            <div className="k">stake_points</div>
            <div className="v">{p.stake_points}</div>
            <div className="k">created</div>
            <div className="v">{fmtTime(p.created_at)}</div>
            <div className="k">updated</div>
            <div className="v">{fmtTime(p.updated_at)}</div>
            <div className="k">description</div>
            <div className="v">{p.description ?? '-'}</div>
          </div>
        ) : (
          <div style={{ color: 'var(--muted)' }}>loading…</div>
        )}
      </div>

      {projectId && (
        <AdminTakeoverProjectModal
          open={showTakeover}
          onClose={() => setShowTakeover(false)}
          projectId={projectId}
          onSuccess={() => load()}
        />
      )}
    </div>
  )
}
