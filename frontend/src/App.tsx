/**
 * App.tsx - 应用根组件
 * 提供 I18n、Theme 两个 Context，并包含顶栏导航和路由。
 */
import { NavLink, Route, Routes } from 'react-router-dom'
import { Dashboard } from './pages/Dashboard'
import { Tasks } from './pages/Tasks'
import { TaskDetail } from './pages/TaskDetail'
import { Leaderboard } from './pages/Leaderboard'
import { Agents } from './pages/Agents'
import { ProjectDetail } from './pages/ProjectDetail'
import { Admin } from './pages/Admin'
import { I18nProvider, useI18n } from './i18n'
import { ThemeProvider, useTheme } from './theme'
import { useEffect, useState } from 'react'

/** 包含语言/主题切换的顶栏 */
function TopBar() {
  const { t, lang, setLang } = useI18n()
  const { theme, setTheme } = useTheme()

  const handleConfigApi = () => {
    const current = localStorage.getItem('agent_hub_api_url') || import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
    const next = window.prompt(lang === 'zh' ? '请输入后端 API 地址 (例如 http://127.0.0.1:8000):' : 'Enter Backend API URL (e.g. http://127.0.0.1:8000):', current);

    if (next !== null) {
      if (next.trim() === '') {
        localStorage.removeItem('agent_hub_api_url');
      } else {
        localStorage.setItem('agent_hub_api_url', next.trim());
      }
      window.location.reload();
    }
  }

  return (
    <div className="topbar">
      <div className="topbar-inner">
        <div className="brand">⚡ AgentHub</div>
        <nav className="nav">
          <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : undefined}>
            {t.nav.dashboard}
          </NavLink>
          <NavLink to="/tasks" className={({ isActive }) => isActive ? 'active' : undefined}>
            {t.nav.tasks}
          </NavLink>
          <NavLink to="/agents" className={({ isActive }) => isActive ? 'active' : undefined}>
            {t.nav.agents}
          </NavLink>
          <NavLink to="/leaderboard" className={({ isActive }) => isActive ? 'active' : undefined}>
            {t.nav.leaderboard}
          </NavLink>
          <NavLink to="/admin" className={({ isActive }) => isActive ? 'active' : undefined}>
            {t.nav.admin}
          </NavLink>
        </nav>

        {/* 右侧操作区 */}
        <div className="topbar-actions">
          {/* GitHub 源码 */}
          <a
            href="https://github.com/niudakok-kok/openclaw-agent-hub"
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-sm"
            title="查看源码"
            style={{ textDecoration: 'none' }}
          >
            ⭐ GitHub
          </a>
          {/* 文档外链 */}
          <a
            href="/docs/index.html"
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-sm"
            title="查看项目的开发文档"
            style={{ textDecoration: 'none' }}
          >
            📖 Docs
          </a>
          {/* 语言切换 */}
          <button
            className="btn btn-sm"
            onClick={() => setLang(lang === 'zh' ? 'en' : 'zh')}
            title={t.language.label}
          >
            {lang === 'zh' ? '🌐 EN' : '🌐 中文'}
          </button>
          {/* 主题切换 */}
          <button
            className="btn btn-sm"
            onClick={() => setTheme(theme === 'office' ? 'dark' : 'office')}
            title={t.theme.label}
          >
            {theme === 'office' ? '🌙' : '☀️'}
          </button>
          {/* API 配置 */}
          <button
            className="btn btn-sm"
            onClick={handleConfigApi}
            title={lang === 'zh' ? '配置后端地址' : 'Config Backend URL'}
          >
            ⚙️
          </button>
        </div>
      </div>
    </div>
  )
}

/** 带 Provider 的 App 根（需要在 Provider 内使用 useI18n） */
function AppInner() {
  const [checkingAuth, setCheckingAuth] = useState(true)
  const [authEnabled, setAuthEnabled] = useState(false)
  const [authed, setAuthed] = useState(false)
  const [password, setPassword] = useState('')
  const [authErr, setAuthErr] = useState('')

  const base = localStorage.getItem('agent_hub_api_url') || import.meta.env.VITE_API_URL || ''

  useEffect(() => {
    fetch(`${base}/api/v0.1/auth/status`, { credentials: 'include' })
      .then(r => r.json())
      .then(s => {
        setAuthEnabled(Boolean(s.enabled))
        setAuthed(Boolean(s.authenticated))
        setCheckingAuth(false)
      })
      .catch(() => {
        setCheckingAuth(false)
      })
  }, [base])

  async function login() {
    setAuthErr('')
    try {
      const res = await fetch(`${base}/api/v0.1/auth/login`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      })
      if (!res.ok) {
        throw new Error(await res.text())
      }
      setAuthed(true)
      setPassword('')
    } catch (e) {
      setAuthErr(String(e))
    }
  }

  if (checkingAuth) {
    return <div className="container"><div className="panel">Checking UI auth...</div></div>
  }

  if (authEnabled && !authed) {
    return (
      <div className="container" style={{ maxWidth: 520, marginTop: 60 }}>
        <div className="panel" style={{ display: 'grid', gap: 12 }}>
          <div className="h1" style={{ margin: 0 }}>🔐 Admin UI Login</div>
          <div style={{ color: 'var(--muted)', fontSize: 13 }}>
            请输入管理员强密码后进入管理界面。
          </div>
          <input
            className="input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter admin password"
          />
          {authErr && <div className="error">{authErr}</div>}
          <button className="btn" onClick={login}>登录</button>
        </div>
      </div>
    )
  }

  return (
    <div>
      <TopBar />
      <div className="container">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/tasks" element={<Tasks />} />
          <Route path="/tasks/:taskId" element={<TaskDetail />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
          <Route path="/projects/:projectId" element={<ProjectDetail />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <I18nProvider>
        <AppInner />
      </I18nProvider>
    </ThemeProvider>
  )
}
