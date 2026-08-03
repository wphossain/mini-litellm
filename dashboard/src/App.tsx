import { useState, useEffect, createContext, useContext, useCallback } from 'react'
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom'
import { apiGet, setToken, getAuthHeaders, setToastFn, clearToken } from './api'

import Overview from './pages/Overview'
import Providers from './pages/Providers'
import ApiKeys from './pages/ApiKeys'
import Models from './pages/Models'
import Health from './pages/Health'
import Usage from './pages/Usage'
import Logs from './pages/Logs'
import ConfigEditor from './pages/ConfigEditor'
import Settings from './pages/Settings'

const ThemeCtx = createContext<{ dark: boolean; toggle: () => void }>({ dark: false, toggle: () => {} })
export const useTheme = () => useContext(ThemeCtx)

// Toast
interface Toast { id: number; message: string; type: 'success' | 'error' | 'info' }
let toastId = 0

function ToastContainer() {
  const [toasts, setToasts] = useState<Toast[]>([])

  const addToast = useCallback((msg: string, type: 'success' | 'error' | 'info' = 'info') => {
    const id = ++toastId
    setToasts(prev => [...prev, { id, message: msg, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000)
  }, [])

  useEffect(() => { setToastFn(addToast) }, [addToast])

  if (toasts.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {toasts.map(t => (
        <div key={t.id} className={`animate-fade-in px-4 py-3 rounded-lg shadow-lg text-sm font-medium ${
          t.type === 'success' ? 'bg-green-600 text-white' :
          t.type === 'error' ? 'bg-red-600 text-white' :
          'bg-gray-800 dark:bg-gray-700 text-white'
        }`}>
          {t.type === 'success' && '✓ '}
          {t.type === 'error' && '✕ '}
          {t.type === 'info' && 'ℹ '}
          {t.message}
        </div>
      ))}
    </div>
  )
}

// Login Page
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
      setError('Invalid API key or gateway unreachable')
      clearToken()
    } finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-blue-50 dark:from-gray-900 dark:to-gray-800">
      <div className="card w-full max-w-md mx-4">
        <div className="p-8">
          <div className="text-center mb-8">
            <div className="text-4xl mb-3">⚡</div>
            <h1 className="text-2xl font-bold dark:text-white">Mini LiteLLM</h1>
            <p className="text-gray-500 dark:text-gray-400 mt-1 text-sm">AI Gateway Admin Panel</p>
          </div>
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Admin API Key</label>
              <input
                type="password"
                value={token}
                onChange={e => setTokenLocal(e.target.value)}
                placeholder="Enter your admin API key..."
                className="input"
                autoFocus
              />
            </div>
            {error && <p className="text-red-500 text-sm mb-4">{error}</p>}
            <button type="submit" disabled={loading || !token} className="btn-primary w-full">
              {loading ? (
                <><svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg> Connecting...</>
              ) : 'Sign In'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

// Sidebar
const NAV_ITEMS = [
  { to: '/', label: 'Overview', icon: '📊' },
  { to: '/providers', label: 'Providers', icon: '🔌' },
  { to: '/keys', label: 'API Keys', icon: '🔑' },
  { to: '/models', label: 'Models', icon: '🧠' },
  { to: '/health', label: 'Health', icon: '💚' },
  { to: '/usage', label: 'Usage', icon: '📈' },
  { to: '/logs', label: 'Logs', icon: '📋' },
  { to: '/config', label: 'Config', icon: '📝' },
  { to: '/settings', label: 'Settings', icon: '⚙️' },
]

const NAV_ICONS: Record<string, string> = {
  '/': '📊', '/providers': '🔌', '/keys': '🔑', '/models': '🧠',
  '/health': '💚', '/usage': '📈', '/logs': '📋', '/config': '📝', '/settings': '⚙️',
}

function Sidebar({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  const location = useLocation()
  const { dark, toggle } = useTheme()

  return (
    <aside className={`${collapsed ? 'w-16' : 'w-64'} transition-all duration-200 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col h-screen sticky top-0`}>
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 h-16 border-b border-gray-200 dark:border-gray-700">
        {!collapsed && (
          <div>
            <h2 className="font-bold dark:text-white text-sm">Mini LiteLLM</h2>
            <p className="text-xs text-gray-400">Gateway Admin</p>
          </div>
        )}
        <button onClick={onToggle} className="ml-auto p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            {collapsed ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
            )}
          </svg>
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map(item => {
          const isActive = location.pathname === item.to || 
            (item.to !== '/' && location.pathname.startsWith(item.to))
          return (
            <Link
              key={item.to}
              to={item.to}
              className={`sidebar-link ${isActive ? 'sidebar-link-active' : 'sidebar-link-inactive'}`}
              title={collapsed ? item.label : undefined}
            >
              <span className="text-lg">{item.icon}</span>
              {!collapsed && <span>{item.label}</span>}
            </Link>
          )
        })}
      </nav>

      {/* Bottom */}
      <div className="p-3 border-t border-gray-200 dark:border-gray-700">
        <button
          onClick={toggle}
          className={`sidebar-link sidebar-link-inactive w-full ${collapsed ? 'justify-center' : ''}`}
          title="Toggle theme"
        >
          <span className="text-lg">{dark ? '☀️' : '🌙'}</span>
          {!collapsed && <span>{dark ? 'Light' : 'Dark'} Mode</span>}
        </button>
      </div>
    </aside>
  )
}

// Layout
function AppShell() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  // Mobile: close sidebar on navigate
  const location = useLocation()
  useEffect(() => { setMobileOpen(false) }, [location.pathname])

  return (
    <div className="flex">
      {/* Desktop sidebar */}
      <div className="hidden md:block">
        <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />
      </div>

      {/* Mobile sidebar overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div className="absolute inset-0 bg-black/30" onClick={() => setMobileOpen(false)} />
          <div className="relative z-50">
            <Sidebar collapsed={false} onToggle={() => setMobileOpen(false)} />
          </div>
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 min-h-screen">
        {/* Mobile header */}
        <header className="md:hidden flex items-center gap-3 px-4 h-14 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-30">
          <button onClick={() => setMobileOpen(true)} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <h2 className="font-bold dark:text-white text-sm">Mini LiteLLM</h2>
        </header>

        <div className="p-4 md:p-8 max-w-7xl mx-auto">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/providers" element={<Providers />} />
            <Route path="/keys" element={<ApiKeys />} />
            <Route path="/models" element={<Models />} />
            <Route path="/health" element={<Health />} />
            <Route path="/usage" element={<Usage />} />
            <Route path="/logs" element={<Logs />} />
            <Route path="/config" element={<ConfigEditor />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </div>
    </div>
  )
}

// Root
let _initialized = false

export default function App() {
  const [authed, setAuthed] = useState(() => {
    if (!_initialized) {
      _initialized = true
      return !!getAuthHeaders().Authorization
    }
    return false
  })
  const [dark, setDark] = useState(() => localStorage.getItem('theme') === 'dark' || window.matchMedia('(prefers-color-scheme: dark)').matches)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }, [dark])

  if (!authed) return <Login onLogin={() => setAuthed(true)} />

  return (
    <ThemeCtx.Provider value={{ dark, toggle: () => setDark(!dark) }}>
      <BrowserRouter>
        <ToastContainer />
        <AppShell />
      </BrowserRouter>
    </ThemeCtx.Provider>
  )
}
