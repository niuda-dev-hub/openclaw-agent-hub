/**
 * Agents - Agent 管理页面
 * 显示所有 Agent 的卡片：在线状态、类型、心跳时间。
 * 新增：钱包余额面板（来自 automaton-lifecycle data.json）和充值按钮。
 */
import { useEffect, useState, useCallback } from 'react'
import { apiGet, apiPatch, apiPost } from '../api/client'
import { AgentStatusBadge } from '../components/AgentStatusBadge'
import { EditAgentConfigModal } from '../components/EditAgentConfigModal'
import { useI18n } from '../i18n'
import { fmtTime } from '../lib/format'

export interface AgentRead {
    id: string
    name: string
    description?: string | null
    agent_type: string
    is_enabled: boolean
    created_at: number
    last_heartbeat_at?: number | null
    config?: Record<string, any>
}

interface WalletState {
    balance_usd: number
    lifetime_spent_usd: number
    lifetime_earned_usd: number
    survival_tier: string
}

/** 根据 Survival Tier 返回对应颜色 CSS key */
function tierColor(tier: string): string {
    switch (tier) {
        case 'high': return 'var(--ok)'
        case 'normal': return 'var(--brand)'
        case 'low_compute': return 'var(--warn)'
        case 'critical': return '#ff4d4f'
        case 'dead': return 'var(--muted)'
        default: return 'var(--muted)'
    }
}

/** 单个 Agent 的钱包面板 */
function WalletPanel({ agentId }: { agentId: string }) {
    const [wallet, setWallet] = useState<WalletState | null>(null)
    const [funding, setFunding] = useState(false)
    const [amount, setAmount] = useState('10')
    const [err, setErr] = useState('')

    const loadWallet = useCallback(() => {
        apiGet<WalletState>(`/api/v0.1/agents/${agentId}/wallet`)
            .then(setWallet)
            .catch(() => setWallet(null))
    }, [agentId])

    useEffect(() => { loadWallet() }, [loadWallet])

    const doFund = async () => {
        const amt = parseFloat(amount)
        if (isNaN(amt) || amt <= 0) { setErr('金额必须大于 0'); return }
        setErr('')
        setFunding(true)
        try {
            const updated = await apiPost<WalletState>(`/api/v0.1/agents/${agentId}/wallet/fund`, { amount_usd: amt })
            setWallet(updated)
        } catch (e) {
            setErr(String(e))
        } finally {
            setFunding(false)
        }
    }

    if (!wallet) return null

    return (
        <div style={{
            marginTop: 10,
            padding: '8px 10px',
            borderRadius: 6,
            background: 'var(--bg-alt)',
            border: '1px solid var(--border)',
            fontSize: 12,
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontWeight: 600 }}>💰 钱包余额</span>
                <span style={{ fontWeight: 700, color: wallet.balance_usd > 0 ? 'var(--ok)' : '#ff4d4f' }}>
                    ${wallet.balance_usd.toFixed(4)}
                </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--muted)', marginBottom: 4 }}>
                <span>今日花费</span>
                <span>${wallet.lifetime_spent_usd.toFixed(4)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--muted)', marginBottom: 6 }}>
                <span>累计奖励</span>
                <span style={{ color: 'var(--ok)' }}>+${wallet.lifetime_earned_usd.toFixed(4)}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4, justifyContent: 'space-between' }}>
                <span style={{
                    padding: '1px 6px',
                    borderRadius: 4,
                    background: tierColor(wallet.survival_tier) + '22',
                    color: tierColor(wallet.survival_tier),
                    fontWeight: 600,
                    fontSize: 11,
                }}>
                    {wallet.survival_tier === 'dead' ? '💀 dead' : `⚡ ${wallet.survival_tier}`}
                </span>
                <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                    <input
                        type="number"
                        value={amount}
                        min="0.01"
                        step="1"
                        onChange={(e) => setAmount(e.target.value)}
                        style={{ width: 60, fontSize: 11, padding: '2px 4px', borderRadius: 4, border: '1px solid var(--border)', background: 'var(--bg)', color: 'var(--fg)' }}
                    />
                    <button
                        className="btn btn-sm"
                        onClick={doFund}
                        disabled={funding}
                        style={{ fontSize: 11, padding: '2px 8px' }}
                    >
                        {funding ? '…' : '💸 打钱'}
                    </button>
                </div>
            </div>
            {err && <div style={{ color: '#ff4d4f', fontSize: 11, marginTop: 4 }}>{err}</div>}
        </div>
    )
}

export function Agents() {
    const { t } = useI18n()
    const [agents, setAgents] = useState<AgentRead[]>([])
    const [loading, setLoading] = useState(true)
    const [err, setErr] = useState('')
    const [toggling, setToggling] = useState<string | null>(null)
    const [editingConfigAgent, setEditingConfigAgent] = useState<AgentRead | null>(null)

    const load = useCallback(() => {
        setLoading(true)
        apiGet<AgentRead[]>('/api/v0.1/agents')
            .then(setAgents)
            .catch((e) => setErr(String(e)))
            .finally(() => setLoading(false))
    }, [])

    useEffect(() => { load() }, [load])

    const toggleEnable = async (agent: AgentRead) => {
        setToggling(agent.id)
        try {
            await apiPatch(`/api/v0.1/agents/${agent.id}`, { is_enabled: !agent.is_enabled })
            load()
        } catch (e) {
            setErr(String(e))
        } finally {
            setToggling(null)
        }
    }

    return (
        <div style={{ display: 'grid', gap: 16 }}>
            <div className="panel-header" style={{ margin: 0, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div className="h1" style={{ margin: 0 }}>{t.agents.title}</div>
                <button className="btn" onClick={load} style={{ fontSize: 12 }}>↺ {t.common.refresh}</button>
            </div>

            {err && <div className="error">{err}</div>}

            {loading
                ? <div style={{ color: 'var(--muted)' }}>{t.common.loading}</div>
                : agents.length === 0
                    ? <div style={{ color: 'var(--muted)' }}>{t.common.noData}</div>
                    : (
                        <div className="agents-grid">
                            {agents.map((a) => (
                                <div key={a.id} className="agent-card" style={{ opacity: a.is_enabled ? 1 : 0.6 }}>
                                    {/* 左侧状态指示 */}
                                    <div style={{ paddingTop: 2 }}>
                                        <AgentStatusBadge lastHeartbeatAt={a.last_heartbeat_at} showLabel={false} />
                                    </div>

                                    {/* 主体信息 */}
                                    <div className="agent-card-body" style={{ flex: 1, minWidth: 0 }}>
                                        <div className="agent-card-name">{a.name}</div>
                                        <div className="agent-card-meta">
                                            {a.agent_type}
                                            {a.description && <span> · {a.description}</span>}
                                        </div>

                                        <div style={{ marginTop: 8, display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
                                            <AgentStatusBadge lastHeartbeatAt={a.last_heartbeat_at} />
                                            <span className={`badge ${a.is_enabled ? 'ok' : ''}`}>
                                                {a.is_enabled ? t.common.enabled : t.common.disabled}
                                            </span>
                                        </div>

                                        <div style={{ marginTop: 6, color: 'var(--muted)', fontSize: 11 }}>
                                            {t.agents.colLastSeen}: {a.last_heartbeat_at ? fmtTime(a.last_heartbeat_at) : t.agents.neverSeen}
                                        </div>

                                        {/* 钱包面板 */}
                                        <WalletPanel agentId={a.id} />

                                        {/* 配置信息摘要展示 */}
                                        <div style={{ marginTop: 12, padding: '8px 10px', borderRadius: 6, background: 'var(--bg-alt)', border: '1px solid var(--border)', fontSize: 11, color: 'var(--muted)' }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                                <span style={{ fontWeight: 600 }}>⚙️ Agent Config</span>
                                            </div>
                                            <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontFamily: 'monospace' }}>
                                                {a.config && Object.keys(a.config).length > 0
                                                    ? JSON.stringify(a.config).substring(0, 100) + (JSON.stringify(a.config).length > 100 ? '...' : '')
                                                    : '{} (无配置)'}
                                            </div>
                                        </div>
                                    </div>

                                    {/* 操作 */}
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'flex-end', flexShrink: 0 }}>
                                        <button
                                            className="btn btn-sm"
                                            onClick={() => setEditingConfigAgent(a)}
                                        >
                                            📝 编辑配置
                                        </button>
                                        <button
                                            className={`btn btn-sm ${a.is_enabled ? 'btn-danger' : ''}`}
                                            onClick={() => toggleEnable(a)}
                                            disabled={toggling === a.id}
                                        >
                                            {a.is_enabled ? t.agents.disable : t.agents.enable}
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

            {/* 编辑配置弹窗 */}
            <EditAgentConfigModal
                agent={editingConfigAgent}
                onClose={() => setEditingConfigAgent(null)}
                onSaved={load}
            />
        </div>
    )
}
