import { useState } from 'react'
import { Modal } from './Modal'
import { apiPost } from '../api/client'

interface Props {
  open: boolean
  onClose: () => void
  projectId: string
  onSuccess?: () => void
}

interface ProjectTakeoverRead {
  id: string
  project_id: string
  stake_refund: number
  bonus_reward: number
  reason?: string | null
  admin_id?: string | null
  created_at: number
}

export function AdminTakeoverProjectModal({ open, onClose, projectId, onSuccess }: Props) {
  const [bonus, setBonus] = useState('0')
  const [reason, setReason] = useState('')
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')

  const submit = async () => {
    setErr('')
    setLoading(true)
    try {
      const payload = {
        bonus_reward: Math.max(0, Number(bonus) || 0),
        reason: reason || undefined,
        admin_id: 'admin',
        idempotency_key: String(Date.now()),
      }
      const res = await apiPost<ProjectTakeoverRead>(`/api/v0.1/admin/projects/${projectId}/takeover`, payload)
      setLoading(false)
      onSuccess?.()
      onClose()
      // eslint-disable-next-line no-alert
      alert(`接管成功\n退还质押: ${res.stake_refund}\n奖励: ${res.bonus_reward}`)
    } catch (e) {
      setLoading(false)
      setErr(String(e))
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="管理员接管项目"
      footer={(
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          <button className="btn" onClick={onClose} disabled={loading}>取消</button>
          <button className="btn btn-danger" onClick={submit} disabled={loading}>
            {loading ? '提交中…' : '确认接管'}
          </button>
        </div>
      )}
      maxWidth={560}
    >
      {err && <div className="error" style={{ marginBottom: 8 }}>{err}</div>}

      <div style={{ display: 'grid', gap: 10 }}>
        <div style={{ color: 'var(--muted)', fontSize: 12 }}>
          将项目发布者改为 admin，并退还原发布者质押积分；可额外发放奖励（从系统金库增发）。
        </div>

        <label style={{ display: 'grid', gap: 4 }}>
          <div style={{ fontSize: 12, color: 'var(--muted)' }}>奖励积分（bonus_reward）</div>
          <input
            value={bonus}
            onChange={(e) => setBonus(e.target.value)}
            inputMode="numeric"
            className="input"
            placeholder="0"
          />
        </label>

        <label style={{ display: 'grid', gap: 4 }}>
          <div style={{ fontSize: 12, color: 'var(--muted)' }}>原因（可选）</div>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="input"
            rows={3}
            placeholder="例如：项目很好，管理员接管继续推进，并奖励提出者"
          />
        </label>

        <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--muted)' }}>
          project_id: {projectId}
        </div>
      </div>
    </Modal>
  )
}
