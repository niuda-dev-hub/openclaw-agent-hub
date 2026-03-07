import { useState, useEffect } from 'react'
import { apiPatch } from '../api/client'
import { Modal } from './Modal'

export interface AgentRead {
    id: string
    name: string
    config?: Record<string, any>
    [key: string]: any
}

interface EditAgentConfigModalProps {
    agent: AgentRead | null
    onClose: () => void
    onSaved: () => void
}

export function EditAgentConfigModal({ agent, onClose, onSaved }: EditAgentConfigModalProps) {
    const [viewMode, setViewMode] = useState<'form' | 'json'>('form')
    const [configObj, setConfigObj] = useState<Record<string, any>>({})
    const [configText, setConfigText] = useState('{\n  \n}')
    const [saving, setSaving] = useState(false)
    const [err, setErr] = useState('')

    // New field state
    const [newKey, setNewKey] = useState('')
    const [newValueType, setNewValueType] = useState<'string' | 'number' | 'boolean'>('string')

    useEffect(() => {
        if (agent) {
            const initialObj = agent.config ? { ...agent.config } : {}
            setConfigObj(initialObj)
            setConfigText(JSON.stringify(initialObj, null, 2))
            setViewMode('form')
            setErr('')
        }
    }, [agent])

    if (!agent) return null

    // Sync from JSON to Form
    const handleTrySwitchToForm = () => {
        setErr('')
        try {
            const parsed = JSON.parse(configText)
            if (typeof parsed !== 'object' || Array.isArray(parsed) || parsed === null) {
                setErr('配置必须是一个合法的 JSON 对象')
                return
            }
            setConfigObj(parsed)
            setViewMode('form')
        } catch (e) {
            setErr('JSON 格式不正确，无法切换到表单视图')
        }
    }

    // Sync from Form to JSON
    const handleSwitchToJson = () => {
        setErr('')
        setConfigText(JSON.stringify(configObj, null, 2))
        setViewMode('json')
    }

    const handleSave = async () => {
        setErr('')
        let finalConfig: Record<string, any>

        if (viewMode === 'json') {
            try {
                finalConfig = JSON.parse(configText)
                if (typeof finalConfig !== 'object' || Array.isArray(finalConfig) || finalConfig === null) {
                    setErr('配置必须是一个合法的 JSON 对象')
                    return
                }
            } catch (e) {
                setErr('JSON 格式不正确: ' + String(e))
                return
            }
        } else {
            finalConfig = { ...configObj }
        }

        setSaving(true)
        try {
            await apiPatch(`/api/v0.1/agents/${agent.id}`, { config: finalConfig })
            onSaved()
            onClose()
        } catch (e) {
            setErr(String(e))
        } finally {
            setSaving(false)
        }
    }

    const handleFieldChange = (key: string, val: any) => {
        setConfigObj(prev => ({ ...prev, [key]: val }))
    }

    const handleRemoveField = (key: string) => {
        setConfigObj(prev => {
            const next = { ...prev }
            delete next[key]
            return next
        })
    }

    const handleAddField = () => {
        if (!newKey.trim()) return
        let val: any = ''
        if (newValueType === 'number') val = 0
        if (newValueType === 'boolean') val = false

        setConfigObj(prev => ({ ...prev, [newKey.trim()]: val }))
        setNewKey('')
    }

    return (
        <Modal title={`编辑配置 - ${agent.name}`} onClose={onClose} open={!!agent}>
            <div style={{ padding: 16 }}>

                {/* 模式切换 Tabs */}
                <div style={{ display: 'flex', gap: 8, marginBottom: 16, borderBottom: '1px solid var(--border)', paddingBottom: 8 }}>
                    <button
                        className={`btn btn-sm ${viewMode === 'form' ? 'btn-primary' : ''}`}
                        onClick={viewMode === 'json' ? handleTrySwitchToForm : undefined}
                    >
                        📝 可视化表单
                    </button>
                    <button
                        className={`btn btn-sm ${viewMode === 'json' ? 'btn-primary' : ''}`}
                        onClick={viewMode === 'form' ? handleSwitchToJson : undefined}
                    >
                        👨‍💻 源码 (JSON)
                    </button>
                </div>

                {/* 表单视图 */}
                {viewMode === 'form' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                        {Object.keys(configObj).length === 0 && (
                            <div style={{ color: 'var(--muted)', fontSize: 13, textAlign: 'center', padding: '20px 0' }}>
                                暂无任何配置字段
                            </div>
                        )}

                        {Object.entries(configObj).map(([k, v]) => {
                            const type = typeof v
                            const isComplex = type === 'object' && v !== null
                            return (
                                <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'var(--bg-alt)', padding: '6px 10px', borderRadius: 6, border: '1px solid var(--border)' }}>
                                    <div style={{ width: 150, flexShrink: 0, fontWeight: 600, fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis' }} title={k}>
                                        {k}
                                    </div>
                                    <div style={{ flex: 1 }}>
                                        {type === 'boolean' ? (
                                            <input type="checkbox" checked={v} onChange={e => handleFieldChange(k, e.target.checked)} />
                                        ) : type === 'number' ? (
                                            <input type="number" value={v} onChange={e => handleFieldChange(k, parseFloat(e.target.value))} style={{ width: '100%', padding: '4px 8px', borderRadius: 4, border: '1px solid var(--border)', background: 'var(--bg)', color: 'var(--fg)', fontSize: 13 }} />
                                        ) : isComplex ? (
                                            <div style={{ fontSize: 12, color: 'var(--warn)' }}>不支持在表单中直接编辑复杂嵌套对象，请使用 JSON 模式</div>
                                        ) : (
                                            <input type="text" value={String(v)} onChange={e => handleFieldChange(k, e.target.value)} style={{ width: '100%', padding: '4px 8px', borderRadius: 4, border: '1px solid var(--border)', background: 'var(--bg)', color: 'var(--fg)', fontSize: 13 }} />
                                        )}
                                    </div>
                                    <button className="btn btn-sm btn-danger" onClick={() => handleRemoveField(k)} title="删除字段">×</button>
                                </div>
                            )
                        })}

                        {/* 添加新字段行 */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 12, paddingTop: 12, borderTop: '1px dashed var(--border)' }}>
                            <input
                                type="text"
                                placeholder="新字段键名..."
                                value={newKey}
                                onChange={e => setNewKey(e.target.value)}
                                style={{ flex: 1, padding: '4px 8px', borderRadius: 4, border: '1px solid var(--border)', background: 'var(--bg)', color: 'var(--fg)', fontSize: 13 }}
                            />
                            <select
                                value={newValueType}
                                onChange={e => setNewValueType(e.target.value as any)}
                                style={{ padding: '4px 8px', borderRadius: 4, border: '1px solid var(--border)', background: 'var(--bg)', color: 'var(--fg)', fontSize: 13 }}
                            >
                                <option value="string">文本 (String)</option>
                                <option value="number">数字 (Number)</option>
                                <option value="boolean">布尔 (Boolean)</option>
                            </select>
                            <button className="btn btn-sm" onClick={handleAddField} disabled={!newKey.trim()}>
                                + 添加
                            </button>
                        </div>
                    </div>
                )}

                {/* JSON 视图 */}
                {viewMode === 'json' && (
                    <>
                        <div style={{ marginBottom: 12, fontSize: 13, color: 'var(--muted)' }}>
                            请以合法的 JSON 格式修改 Agent 的配置信息。
                        </div>
                        <textarea
                            value={configText}
                            onChange={(e) => setConfigText(e.target.value)}
                            style={{
                                width: '100%',
                                height: 260,
                                fontFamily: 'monospace',
                                fontSize: 13,
                                padding: 12,
                                borderRadius: 6,
                                border: '1px solid var(--border)',
                                background: 'var(--bg-alt)',
                                color: 'var(--fg)',
                                resize: 'vertical'
                            }}
                            spellCheck={false}
                        />
                    </>
                )}

                {err && <div className="error" style={{ marginTop: 12 }}>{err}</div>}

                <div style={{ marginTop: 20, display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
                    <button className="btn" onClick={onClose} disabled={saving}>
                        取消
                    </button>
                    <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                        {saving ? '保存中...' : '保存配置'}
                    </button>
                </div>
            </div>
        </Modal>
    )
}
