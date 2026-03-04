/** 格式化时间戳（毫秒或 ISO 字符串）为本地时间字符串 */
export function fmtTime(msOrIso: number | string | null | undefined): string {
  if (msOrIso == null) return '-'
  try {
    const d = typeof msOrIso === 'number' ? new Date(msOrIso) : new Date(msOrIso)
    if (Number.isNaN(d.getTime())) return String(msOrIso)
    return d.toLocaleString()
  } catch {
    return String(msOrIso)
  }
}

/** 截断 ID 前 n 位 */
export function shortId(id: string, n = 8): string {
  if (!id) return ''
  return id.length <= n ? id : `${id.slice(0, n)}…`
}

/** 根据任务/run 状态返回 CSS 徽章类名 */
export function statusClass(status: string | null | undefined): 'ok' | 'warn' | 'bad' | 'info' | '' {
  const s = (status ?? '').toLowerCase()
  if (!s) return ''
  // 绿色：完成
  if (['finalized', 'finished', 'done', 'success', 'completed'].includes(s)) return 'ok'
  // 黄色：进行中/排队
  if (['running', 'in_progress', 'active', 'queued'].includes(s)) return 'warn'
  // 红色：失败/取消
  if (['failed', 'error', 'cancelled'].includes(s)) return 'bad'
  // 蓝色：草稿/开放
  if (['draft', 'open', 'pending'].includes(s)) return 'info'
  return ''
}
