/**
 * CreateTaskModal - 创建新任务的弹窗
 * 调用 POST /tasks，成功后回调刷新列表
 */
import { useState } from 'react'
import { Modal } from './Modal'
import { apiPost } from '../api/client'
import { useI18n } from '../i18n'

interface TaskCreate {
    title: string
    prompt: string
    expected_output_type: string
    created_by?: string
}

interface CreateTaskModalProps {
    open: boolean
    onClose: () => void
    /** 创建成功后的回调（可用于刷新任务列表） */
    onSuccess?: (taskId: string) => void
}

export function CreateTaskModal({ open, onClose, onSuccess }: CreateTaskModalProps) {
    const { t } = useI18n()

    const [form, setForm] = useState<TaskCreate>({
        title: '',
        prompt: '',
        expected_output_type: 'text',
        created_by: '',
    })
    const [submitting, setSubmitting] = useState(false)
    const [err, setErr] = useState('')

    const handleChange = (field: keyof TaskCreate, val: string) => {
        setForm((prev) => ({ ...prev, [field]: val }))
    }

    const handleSubmit = async () => {
        if (!form.title.trim() || !form.prompt.trim()) {
            setErr('标题和描述不能为空')
            return
        }
        setSubmitting(true)
        setErr('')
        try {
            const result = await apiPost<{ id: string }>('/api/v0.1/tasks', {
                title: form.title.trim(),
                prompt: form.prompt.trim(),
                expected_output_type: form.expected_output_type,
                created_by: form.created_by?.trim() || undefined,
            })
            // 重置表单
            setForm({ title: '', prompt: '', expected_output_type: 'text', created_by: '' })
            onSuccess?.(result.id)
            onClose()
        } catch (e) {
            setErr(String(e))
        } finally {
            setSubmitting(false)
        }
    }

    const footer = (
        <>
            <button className="btn" onClick={onClose} disabled={submitting}>{t.common.cancel}</button>
            <button
                className="btn btn-primary"
                onClick={handleSubmit}
                disabled={submitting}
            >
                {submitting ? t.common.loading : t.common.create}
            </button>
        </>
    )

    return (
        <Modal open={open} onClose={onClose} title={t.createTask.title} footer={footer} maxWidth={520}>
            {err && <div className="error" style={{ marginBottom: 10 }}>{err}</div>}

            <div className="form-group">
                <label className="form-label">{t.createTask.fieldTitle} *</label>
                <input
                    className="form-control"
                    value={form.title}
                    onChange={(e) => handleChange('title', e.target.value)}
                    placeholder={t.createTask.fieldTitlePlaceholder}
                />
            </div>

            <div className="form-group">
                <label className="form-label">{t.createTask.fieldPrompt} *</label>
                <textarea
                    className="form-control"
                    value={form.prompt}
                    onChange={(e) => handleChange('prompt', e.target.value)}
                    placeholder={t.createTask.fieldPromptPlaceholder}
                    rows={4}
                />
            </div>

            <div className="form-group">
                <label className="form-label">{t.createTask.fieldOutputType}</label>
                <select
                    className="form-control"
                    value={form.expected_output_type}
                    onChange={(e) => handleChange('expected_output_type', e.target.value)}
                >
                    <option value="text">{t.createTask.outputTypeText}</option>
                    <option value="code">{t.createTask.outputTypeCode}</option>
                    <option value="file">{t.createTask.outputTypeFile}</option>
                </select>
            </div>

            <div className="form-group">
                <label className="form-label">{t.createTask.fieldCreatedBy}</label>
                <input
                    className="form-control"
                    value={form.created_by}
                    onChange={(e) => handleChange('created_by', e.target.value)}
                    placeholder={t.createTask.fieldCreatedByPlaceholder}
                />
            </div>
        </Modal>
    )
}
