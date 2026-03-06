/**
 * Leaderboard - 排行榜页面
 * 从所有任务聚合评分，展示全局 Agent 得分排行。
 */
import { useEffect, useState } from 'react'
import { apiGet } from '../api/client'
import { useI18n } from '../i18n'
import { shortId } from '../lib/format'

interface TaskRead { id: string; title: string; status: string }
interface LeaderboardEntry { submission_id: string; avg_reward_usd: number; review_count: number }

interface Row extends LeaderboardEntry {
  taskId: string
  taskTitle: string
}

export function Leaderboard() {
  const { t } = useI18n()
  const [rows, setRows] = useState<Row[]>([])
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState('')

  useEffect(() => {
    // 加载所有任务，然后并发获取各任务的 leaderboard
    apiGet<TaskRead[]>('/api/v0.1/tasks')
      .then(async (tasks) => {
        const results = await Promise.allSettled(
          tasks
            .filter((t) => ['running', 'finalized'].includes(t.status))
            .map((task) =>
              apiGet<LeaderboardEntry[]>(`/api/v0.1/tasks/${task.id}/leaderboard`).then((entries) =>
                entries.map((e) => ({ ...e, taskId: task.id, taskTitle: task.title }))
              )
            )
        )
        const all: Row[] = []
        results.forEach((r) => { if (r.status === 'fulfilled') all.push(...r.value) })
        // 按平均分降序
        all.sort((a, b) => b.avg_reward_usd - a.avg_reward_usd)
        setRows(all)
        setLoading(false)
      })
      .catch((e) => { setErr(String(e)); setLoading(false) })
  }, [])

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <div className="h1" style={{ margin: 0 }}>{t.leaderboard.title}</div>
      {err && <div className="error">{err}</div>}
      {loading && <div style={{ color: 'var(--muted)' }}>{t.common.loading}</div>}
      {!loading && rows.length === 0 && (
        <div className="panel" style={{ color: 'var(--muted)', textAlign: 'center', padding: '32px 0' }}>
          {t.leaderboard.noData}
        </div>
      )}
      {rows.length > 0 && (
        <div className="panel" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="table">
            <thead>
              <tr>
                <th style={{ paddingLeft: 16, width: 40 }}>#</th>
                <th>submission</th>
                <th>{t.leaderboard.colTask}</th>
                <th>💰 avg reward (USD)</th>
                <th>{t.leaderboard.colReviews}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr key={row.submission_id}>
                  <td style={{ paddingLeft: 16, color: 'var(--muted)', fontWeight: 600 }}>
                    {i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : i + 1}
                  </td>
                  <td style={{ fontFamily: 'var(--mono)', fontSize: 12 }}>
                    {shortId(row.submission_id, 12)}
                  </td>
                  <td style={{ fontSize: 13 }}>{row.taskTitle}</td>
                  <td>
                    <span style={{ fontWeight: 700, fontSize: 15, color: 'var(--ok)' }}>
                      ${row.avg_reward_usd.toFixed(4)}
                    </span>
                  </td>
                  <td style={{ color: 'var(--muted)' }}>{row.review_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
