/**
 * 主题 Context
 * 支持 office（默认）和 dark 主题，通过 localStorage 持久化。
 * 主题通过 <html data-theme="..."> 应用 CSS 变量。
 */
import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'

export type Theme = 'office' | 'dark'

interface ThemeContextValue {
    theme: Theme
    setTheme: (t: Theme) => void
}

const ThemeContext = createContext<ThemeContextValue>({
    theme: 'office',
    setTheme: () => { },
})

function applyTheme(t: Theme) {
    document.documentElement.setAttribute('data-theme', t)
}

export function ThemeProvider({ children }: { children: ReactNode }) {
    const [theme, setThemeState] = useState<Theme>(() => {
        const saved = localStorage.getItem('aghub_theme') as Theme | null
        const t = (saved === 'dark' || saved === 'office') ? saved : 'office'
        applyTheme(t)
        return t
    })

    const setTheme = useCallback((t: Theme) => {
        localStorage.setItem('aghub_theme', t)
        applyTheme(t)
        setThemeState(t)
    }, [])

    return (
        <ThemeContext.Provider value={{ theme, setTheme }}>
            {children}
        </ThemeContext.Provider>
    )
}

export function useTheme() {
    return useContext(ThemeContext)
}
