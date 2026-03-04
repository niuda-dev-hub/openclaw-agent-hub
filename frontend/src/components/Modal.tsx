/**
 * 通用 Modal 弹窗组件
 * - Portal 渲染到 body
 * - Escape 键关闭
 * - 遮罩层点击关闭
 */
import { useEffect, type ReactNode } from 'react'
import { createPortal } from 'react-dom'

interface ModalProps {
    /** 是否显示 */
    open: boolean
    /** 关闭回调 */
    onClose: () => void
    /** 弹窗标题 */
    title: string
    /** 底部操作栏内容 */
    footer?: ReactNode
    children: ReactNode
    /** 最大宽度，默认 480px */
    maxWidth?: number
}

export function Modal({ open, onClose, title, footer, children, maxWidth = 480 }: ModalProps) {
    // Escape 关闭
    useEffect(() => {
        if (!open) return
        const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
        window.addEventListener('keydown', handler)
        return () => window.removeEventListener('keydown', handler)
    }, [open, onClose])

    if (!open) return null

    return createPortal(
        <div
            className="modal-overlay"
            onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
        >
            <div className="modal-box" style={{ maxWidth }}>
                <div className="modal-header">
                    <span className="modal-title">{title}</span>
                    <button
                        className="btn btn-sm"
                        onClick={onClose}
                        aria-label="关闭"
                        style={{ padding: '2px 6px', lineHeight: 1 }}
                    >✕</button>
                </div>
                <div className="modal-body">
                    {children}
                </div>
                {footer && (
                    <div className="modal-footer">
                        {footer}
                    </div>
                )}
            </div>
        </div>,
        document.body,
    )
}
