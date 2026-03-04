/**
 * AgentStatusBadge - 根据 last_heartbeat_at 显示 Agent 在线状态
 *
 * 规则（与后端独立，纯前端计算）：
 *   - last_heartbeat_at 为 null → offline（从未上报）
 *   - 距今 < 5 分钟   → online（在线）
 *   - 距今 < 30 分钟  → idle（空闲）
 *   - 距今 >= 30 分钟 → offline（离线）
 */
import { useI18n } from '../i18n'

export type OnlineStatus = 'online' | 'idle' | 'offline'

/** 根据心跳时间戳计算在线状态 */
export function calcOnlineStatus(lastHeartbeatAt: number | null | undefined): OnlineStatus {
    if (!lastHeartbeatAt) return 'offline'
    const diffMs = Date.now() - lastHeartbeatAt
    if (diffMs < 5 * 60 * 1000) return 'online'
    if (diffMs < 30 * 60 * 1000) return 'idle'
    return 'offline'
}

interface AgentStatusBadgeProps {
    lastHeartbeatAt?: number | null
    /** 可选：覆盖自动计算的状态 */
    status?: OnlineStatus
    showLabel?: boolean
}

export function AgentStatusBadge({ lastHeartbeatAt, status, showLabel = true }: AgentStatusBadgeProps) {
    const { t } = useI18n()
    const s = status ?? calcOnlineStatus(lastHeartbeatAt)

    const cls = s === 'online' ? 'ok' : s === 'idle' ? 'warn' : ''
    const label = t.status[s]

    return (
        <span className={`badge ${cls}`} style={{ display: 'inline-flex', alignItems: 'center' }}>
            <span className={`status-dot ${s}`} />
            {showLabel && label}
        </span>
    )
}
