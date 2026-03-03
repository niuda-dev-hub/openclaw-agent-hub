import { Link, Route, Routes } from 'react-router-dom'
import { Dashboard } from './pages/Dashboard'
import { Tasks } from './pages/Tasks'
import { TaskDetail } from './pages/TaskDetail'
import { Leaderboard } from './pages/Leaderboard'

export default function App() {
  return (
    <div>
      <header style={{ padding: 16, borderBottom: '1px solid #eee', display: 'flex', gap: 12 }}>
        <strong>AgentHub Admin</strong>
        <Link to="/">Dashboard</Link>
        <Link to="/tasks">Tasks</Link>
        <Link to="/leaderboard">Leaderboard</Link>
      </header>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/tasks" element={<Tasks />} />
        <Route path="/tasks/:taskId" element={<TaskDetail />} />
        <Route path="/leaderboard" element={<Leaderboard />} />
      </Routes>
    </div>
  )
}
