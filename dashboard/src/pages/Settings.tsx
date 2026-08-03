import { useState, useEffect } from 'react'
import { useTheme } from '../App'
import { apiGet, apiPost, getAuthHeaders, clearToken } from '../api'

export default function Settings() {
  const { dark, toggle } = useTheme()
  const [msg, setMsg] = useState('')
  const [health, setHealth] = useState<any>(null)

  useEffect(() => {
    apiGet('/health').then(setHealth).catch(() => {})
  }, [])

  async function reloadAll() {
    await apiPost('/admin/providers/reload')
    setMsg('Configuration reloaded from disk')
    setTimeout(() => setMsg(''), 3000)
  }

  async function handleLogout() {
    clearToken()
    window.location.reload()
  }

  return (
    <div className="animate-fade-in max-w-2xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold dark:text-white">Settings</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Gateway configuration and preferences</p>
      </div>

      {msg && <div className="mb-4 px-4 py-3 rounded-lg text-sm font-medium bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 border border-green-200 dark:border-green-800">✓ {msg}</div>}

      <div className="card mb-4">
        <div className="card-header">Appearance</div>
        <div className="card-body">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium dark:text-white">Dark Mode</div>
              <p className="text-sm text-gray-500">Toggle dark/light theme</p>
            </div>
            <button onClick={toggle} className={`relative w-12 h-6 rounded-full transition-colors ${dark ? 'bg-blue-600' : 'bg-gray-300'}`}>
              <span className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${dark ? 'translate-x-6' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      <div className="card mb-4">
        <div className="card-header">Configuration</div>
        <div className="card-body space-y-4">
          <div>
            <div className="font-medium dark:text-white">Reload from Disk</div>
            <p className="text-sm text-gray-500 mb-3">Reload config.yaml without restarting the server</p>
            <button onClick={reloadAll} className="btn-primary">🔄 Reload Now</button>
          </div>
          <hr className="border-gray-200 dark:border-gray-700" />
          <div>
            <div className="font-medium dark:text-white">Environment</div>
            <p className="text-sm text-gray-500">
              {health ? (
                <>Uptime: {Math.floor(health.uptime_seconds / 60)}m {Math.floor(health.uptime_seconds % 60)}s</>
              ) : 'Loading...'}
            </p>
          </div>
        </div>
      </div>

      <div className="card mb-4">
        <div className="card-header">Account</div>
        <div className="card-body flex items-center justify-between">
          <div>
            <div className="font-medium dark:text-white">Admin Session</div>
            <p className="text-sm text-gray-500">Sign out of the admin panel</p>
          </div>
          <button onClick={handleLogout} className="btn-danger">🚪 Sign Out</button>
        </div>
      </div>

      <div className="card">
        <div className="card-header">About</div>
        <div className="card-body space-y-1 text-sm">
          <div className="flex justify-between"><span className="text-gray-500">Version</span><span className="font-medium">1.0.0</span></div>
          <div className="flex justify-between"><span className="text-gray-500">Framework</span><span>FastAPI + LiteLLM SDK</span></div>
          <div className="flex justify-between"><span className="text-gray-500">Dashboard</span><span>React + Vite + Tailwind</span></div>
          <div className="flex justify-between"><span className="text-gray-500">Deployment</span><span>Northflank / Docker</span></div>
        </div>
      </div>
    </div>
  )
}
