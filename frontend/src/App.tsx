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

/** 包含语言/主题切换的顶栏 */
function TopBar() {
  const { t, lang, setLang } = useI18n()
  const { theme, setTheme } = useTheme()

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
        </div>
      </div>
    </div>
  )
}

/** 带 Provider 的 App 根（需要在 Provider 内使用 useI18n） */
function AppInner() {
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
