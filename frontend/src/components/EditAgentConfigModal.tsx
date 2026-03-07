import { useState } from 'react'
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
    // 默认展示漂亮的格式化 JSON
    const [configText, setConfigText] = useState(() =>
        agent?.config ? JSON.stringify(agent.config, null, 2) : '{\n  \n}'
    )
    const [saving, setSaving] = useState(false)
    const [err, setErr] = useState('')

    if (!agent) return null

    const handleSave = async () => {
        setErr('')
        let parsedConfig: Record<string, any>
        try {
            parsedConfig = JSON.parse(configText)
        } catch (e) {
            setErr('JSON 格式不正确: ' + String(e))
            return
        }

        setSaving(true)
        try {
            await apiPatch(`/api/v0.1/agents/${agent.id}`, { config: parsedConfig })
            onSaved()
            onClose()
        } catch (e) {
            setErr(String(e))
        } finally {
            setSaving(false)
        }
    }

    return (
        <Modal title={`编辑配置 - ${agent.name}`} onClose={onClose} open={!!agent}>
            <div style={{ padding: 16 }}>
                <div style={{ marginBottom: 12, fontSize: 13, color: 'var(--muted)' }}>
                    请以合法的 JSON 格式修改 Agent 的静态配置信息。
                </div>

                <textarea
                    value={configText}
                    onChange={(e) => setConfigText(e.target.value)}
                    style={{
                        width: '100%',
                        height: 200,
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
