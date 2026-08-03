import { useState, useEffect, createContext, useContext } from 'react'
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom'
import { apiGet, setToken, getAuthHeaders } from './api'
import Providers from './pages/Providers'
import Models from './pages/Models'
import ApiKeys from './pages/ApiKeys'
import Usage from './pages/Usage'
import Health from './pages/Health'
import Logs from './pages/Logs'
import Settings from './pages/Settings'

const ThemeCtx = createContext<{ dark: boolean; toggle: () => void }>({ dark: false, toggle: () => {} })
export const useTheme = () => useContext(ThemeCtx)

function Login({ onLogin }: { onLogin: (t: string) => void }) {
  const [token, setTokenLocal] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      setToken(token)
      await apiGet('/health')
      onLogin(token)
    } catch {
      setError('Invalid token or gateway unreachable')
    } finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900">
      <div className="card w-full max-w-md">
        <h1 className="text-2xl font-bold mb-2 dark:text-white">Mini LiteLLM</h1>
        <p className="text-gray-500 dark:text-gray-400 mb-6">Enter your admin API key to continue</p>
        <form onSubmit={handleSubmit}>
          <input
            type="password" value={token} onChange={e => setTokenLocal(e.target.value)}
            placeholder="sk-master-key-change-me"
            className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white mb-4"
          />
          {error && <p className="text-red-500 text-sm mb-4">{error}</p>}
          <button type="submit" disabled={loading || !token} className="btn btn-primary w-full">
            {loading ? 'Connecting...' : 'Login'}
          </button>
        </form>
      </div>
    </div>
  )
}

const NAV = [
  { to: '/providers', label: 'Providers', icon: '🔌' },
  { to: '/models', label: 'Models', icon: '🧠' },
  { to: '/keys', label: 'API Keys', icon: '🔑' },
  { to: '/usage', label: 'Usage', icon: '📊' },
  { to: '/health', label: 'Health', icon: '💚' },
  { to: '/logs', label: 'Logs', icon: '📋' },
  { to: '/settings', label: 'Settings', icon: '⚙️' },
]

function Layout({ children }: { children: React.ReactNode }) {
  const { dark, toggle } = useTheme()
  const location = useLocation()

  return (
    <div className="min-h-screen flex">
      <aside className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
        <div className="p-5 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-bold dark:text-white">⚡ Mini LiteLLM</h2>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {NAV.map(item => (
            <Link key={item.to} to={item.to} className={`sidebar-link ${location.pathname === item.to ? 'sidebar-link-active' : 'sidebar-link-inactive'}`}>
              <span>{item.icon}</span><span>{item.label}</span>
            </Link>
          ))}
        </nav>
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <button onClick={toggle} className="btn btn-outline w-full text-sm">
            {dark ? '☀️ Light' : '🌙 Dark'}
          </button>
        </div>
      </aside>
      <main className="flex-1 p-6 overflow-auto">{children}</main>
    </div>
  )
}

function AppShell() {
  return (
    <Layout>
      <Routes>
        <Route path="/providers" element={<Providers />} />
        <Route path="/models" element={<Models />} />
        <Route path="/keys" element={<ApiKeys />} />
        <Route path="/usage" element={<Usage />} />
        <Route path="/health" element={<Health />} />
        <Route path="/logs" element={<Logs />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/providers" replace />} />
      </Routes>
    </Layout>
  )
}

export default function App() {
  const [authed, setAuthed] = useState(!!getAuthHeaders().Authorization)
  const [dark, setDark] = useState(() => localStorage.getItem('theme') === 'dark' || window.matchMedia('(prefers-color-scheme: dark)').matches)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }, [dark])

  function handleLogin() { setAuthed(true) }

  if (!authed) return <Login onLogin={handleLogin} />

  return (
    <ThemeCtx.Provider value={{ dark, toggle: () => setDark(!dark) }}>
      <BrowserRouter><AppShell /></BrowserRouter>
    </ThemeCtx.Provider>
  )
}
