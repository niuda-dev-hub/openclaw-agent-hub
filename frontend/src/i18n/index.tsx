/**
 * 多语言（i18n）Context
 * 支持中文（默认）和英文，通过 localStorage 持久化用户选择。
 */
import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'
import { zh } from './zh'
import { en } from './en'
import type { Translations } from './zh'

export type Lang = 'zh' | 'en'

const translations: Record<Lang, Translations> = { zh, en }

interface I18nContextValue {
    lang: Lang
    t: Translations
    setLang: (l: Lang) => void
}

const I18nContext = createContext<I18nContextValue>({
    lang: 'zh',
    t: zh,
    setLang: () => { },
})

/** i18n Provider，包裹 App 根节点即可 */
export function I18nProvider({ children }: { children: ReactNode }) {
    const [lang, setLangState] = useState<Lang>(() => {
        const saved = localStorage.getItem('aghub_lang')
        return (saved === 'en' || saved === 'zh') ? saved : 'zh'
    })

    const setLang = useCallback((l: Lang) => {
        localStorage.setItem('aghub_lang', l)
        setLangState(l)
    }, [])

    return (
        <I18nContext.Provider value={{ lang, t: translations[lang], setLang }}>
            {children}
        </I18nContext.Provider>
    )
}

/** 在任意组件中使用翻译 */
export function useI18n() {
    return useContext(I18nContext)
}
