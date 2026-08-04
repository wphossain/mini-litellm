import { useState, useEffect, createContext, useContext, useCallback } from 'react'
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom'
import { apiGet, setToken, getAuthHeaders, setToastFn, clearToken } from './api'
import { ApiProvider, useApi } from './api'

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

export default function App() {
  const [authed, setAuthed] = useState(() => !!getAuthHeaders().Authorization)
  const [dark, setDark] = useState(() => localStorage.getItem('theme') === 'dark')

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }, [dark])

  const handleLogin = (t: string) => { setToken(t); setAuthed(true) }

  return (
    <ApiProvider>
      <ThemeCtx.Provider value={{ dark, toggle: () => setDark(!dark) }}>
        <BrowserRouter basename="/admin/ui">
          <AppInner authed={authed} onLogin={handleLogin} />
        </BrowserRouter>
      </ThemeCtx.Provider>
    </ApiProvider>
  )
}

function AppInner({ authed, onLogin }: { authed: boolean; onLogin: (t: string) => void }) {
  const { apiGet } = useApi()
  const [toasts, setToasts] = useState<{ id: number; msg: string; type: string }[]>([])

  const showToast = useCallback((msg: string, type: string = 'success') => {
    const id = Date.now()
    setToasts(prev => [...prev, { id, msg, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3500)
  }, [])

  useEffect(() => { setToastFn(showToast) }, [setToastFn, showToast])

  if (!authed) {
    return (
      <>
        <Login onLogin={onLogin} />
        <Toasts toasts={toasts} />
      </>
    )
  }

  const doLogout = () => { clearToken(); window.location.reload() }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 overflow-x-hidden">
        <div className="p-6 md:p-8 max-w-7xl mx-auto">
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
      </main>
      <Toasts toasts={toasts} />
    </div>
  )
}
