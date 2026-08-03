import { useState, useEffect } from 'react'
import { useTheme } from '../App'
import { apiGet, apiPost, apiPut } from '../api'

export default function Settings() {
  const { dark, toggle } = useTheme()
  const [msg, setMsg] = useState('')
  const [yaml, setYaml] = useState('')
  const [editing, setEditing] = useState(false)

  useEffect(() => { loadConfig() }, [])

  async function loadConfig() {
    try {
      const d = await apiGet('/admin/config')
      setYaml(d.config || '')
    } catch { setYaml('Cannot load config (Vercel mode)') }
  }

  async function saveYaml() {
    await apiPut('/admin/config', { config: yaml })
    setMsg('Configuration saved to disk!')
    setEditing(false)
  }

  async function reloadProviders() {
    await apiPost('/admin/providers/reload')
    setMsg('Providers reloaded from config.yaml')
  }

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-bold mb-6 dark:text-white">Settings</h1>
      {msg && <p className="text-green-500 mb-4 bg-green-50 dark:bg-green-900/20 px-4 py-2 rounded-lg">{msg}</p>}
      
      <div className="card mb-4">
        <h3 className="font-semibold mb-3 dark:text-white">Appearance</h3>
        <button onClick={toggle} className="btn btn-outline">{dark ? '☀️ Switch to Light' : '🌙 Switch to Dark'}</button>
      </div>
      
      <div className="card mb-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold dark:text-white">Configuration (config.yaml)</h3>
          <div className="flex gap-2">
            {!editing ? (
              <button onClick={() => setEditing(true)} className="btn btn-primary">Edit YAML</button>
            ) : (
              <>
                <button onClick={saveYaml} className="btn btn-primary">💾 Save</button>
                <button onClick={() => setEditing(false)} className="btn btn-outline">Cancel</button>
              </>
            )}
          </div>
        </div>
        <p className="text-sm text-gray-400 mb-3">
          Changes save directly to config.yaml. Gateway auto-reloads on save.
          {!editing && ' Click "Edit YAML" to modify.'}
        </p>
        {editing && (
          <textarea
            value={yaml}
            onChange={e => setYaml(e.target.value)}
            className="w-full h-96 font-mono text-sm p-4 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-200"
            spellCheck={false}
          />
        )}
      </div>

      <div className="card mb-4">
        <h3 className="font-semibold mb-3 dark:text-white">Actions</h3>
        <div className="flex gap-3 flex-wrap">
          <button onClick={reloadProviders} className="btn btn-primary">🔄 Reload Config</button>
        </div>
      </div>

      <div className="card">
        <h3 className="font-semibold mb-3 dark:text-white">About</h3>
        <p className="text-sm text-gray-400">Mini LiteLLM Gateway v1.0.0</p>
        <p className="text-sm text-gray-400">Built with LiteLLM SDK • FastAPI • React + Tailwind</p>
        <p className="text-sm text-gray-400 mt-2">
          Run locally: <code className="bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded">docker compose up -d</code>
        </p>
      </div>
    </div>
  )
}
