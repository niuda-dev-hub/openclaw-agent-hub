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

export function shortId(id: string, n = 8): string {
  if (!id) return ''
  return id.length <= n ? id : `${id.slice(0, n)}…`
}

export function statusClass(status: string | null | undefined): 'ok' | 'warn' | 'bad' | '' {
  const s = (status ?? '').toLowerCase()
  if (!s) return ''
  if (['done', 'success', 'completed'].includes(s)) return 'ok'
  if (['running', 'in_progress', 'active'].includes(s)) return 'warn'
  if (['failed', 'error'].includes(s)) return 'bad'
  if (['draft', 'pending'].includes(s)) return ''
  return ''
}
