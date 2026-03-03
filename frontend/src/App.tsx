import { NavLink, Route, Routes } from 'react-router-dom'
import { Dashboard } from './pages/Dashboard'
import { Tasks } from './pages/Tasks'
import { TaskDetail } from './pages/TaskDetail'
import { Leaderboard } from './pages/Leaderboard'

export default function App() {
  return (
    <div>
      <div className="topbar">
        <div className="container topbar-inner">
          <div className="brand">AgentHub Admin</div>
          <nav className="nav">
            <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : undefined)}>
              Dashboard
            </NavLink>
            <NavLink to="/tasks" className={({ isActive }) => (isActive ? 'active' : undefined)}>
              Tasks
            </NavLink>
            <NavLink to="/leaderboard" className={({ isActive }) => (isActive ? 'active' : undefined)}>
              Leaderboard
            </NavLink>
          </nav>
        </div>
      </div>

      <div className="container">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/tasks" element={<Tasks />} />
          <Route path="/tasks/:taskId" element={<TaskDetail />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
        </Routes>
      </div>
    </div>
  )
}
