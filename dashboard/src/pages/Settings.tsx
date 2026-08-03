import { useState } from 'react'
import { useTheme } from '../App'
import { apiPost } from '../api'

export default function Settings() {
  const { dark, toggle } = useTheme()
  const [msg, setMsg] = useState('')

  async function reloadProviders() {
    await apiPost('/admin/providers/reload')
    setMsg('Providers reloaded from disk')
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6 dark:text-white">Settings</h1>
      {msg && <p className="text-green-500 mb-4">{msg}</p>}
      <div className="card mb-4">
        <h3 className="font-semibold mb-3 dark:text-white">Appearance</h3>
        <button onClick={toggle} className="btn btn-outline">{dark ? '☀️ Switch to Light' : '🌙 Switch to Dark'}</button>
      </div>
      <div className="card mb-4">
        <h3 className="font-semibold mb-3 dark:text-white">Configuration</h3>
        <p className="text-sm text-gray-400 mb-3">Reload config.yaml from disk without restarting.</p>
        <button onClick={reloadProviders} className="btn btn-primary">Reload Config</button>
      </div>
      <div className="card">
        <h3 className="font-semibold mb-3 dark:text-white">About</h3>
        <p className="text-sm text-gray-400">Mini LiteLLM Gateway v1.0.0</p>
        <p className="text-sm text-gray-400">Built with LiteLLM SDK • FastAPI • React + Tailwind</p>
      </div>
    </div>
  )
}
