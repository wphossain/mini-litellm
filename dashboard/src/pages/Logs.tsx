import { useState, useEffect } from 'react'
import { apiGet } from '../api'

export default function Logs() {
  const [logs, setLogs] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => { load() }, [])

  async function load() {
    setLoading(true)
    try {
      const d = await apiGet('/admin/logs?limit=100')
      setLogs(d.logs || [])
      setTotal(d.total)
    } catch {}
    setLoading(false)
  }

  const filtered = logs.filter(l =>
    !search || l.method?.toLowerCase().includes(search.toLowerCase()) ||
    l.path?.toLowerCase().includes(search.toLowerCase()) ||
    l.provider?.toLowerCase().includes(search.toLowerCase()) ||
    l.model?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold dark:text-white">Logs</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{total} total requests</p>
        </div>
        <button onClick={load} className="btn-secondary" disabled={loading}>
          {loading ? (
            <><svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg> Loading...</>
          ) : '🔄 Refresh'}
        </button>
      </div>

      <div className="mb-4">
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search logs by method, path, provider, model..." className="input max-w-md" />
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto max-h-[70vh] overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-white dark:bg-gray-800">
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="table-header pl-6">Time</th><th className="table-header">Method</th><th className="table-header">Path</th><th className="table-header">Provider</th><th className="table-header">Model</th><th className="table-header">Status</th><th className="table-header">Latency</th><th className="table-header pr-6">Tokens</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((l, i) => (
                <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                  <td className="table-cell pl-6 text-gray-500 text-xs whitespace-nowrap">{new Date(l.timestamp).toLocaleTimeString()}</td>
                  <td className="table-cell"><span className="badge badge-blue">{l.method}</span></td>
                  <td className="table-cell text-xs font-mono text-gray-600 dark:text-gray-400 max-w-[200px] truncate" title={l.path}>{l.path}</td>
                  <td className="table-cell">{l.provider || <span className="text-gray-400">-</span>}</td>
                  <td className="table-cell text-xs max-w-[150px] truncate" title={l.model}>{l.model || <span className="text-gray-400">-</span>}</td>
                  <td className="table-cell"><span className={`badge ${l.status_code < 400 ? 'badge-green' : 'badge-red'}`}>{l.status_code}</span></td>
                  <td className="table-cell">{l.latency_ms?.toFixed(0) || '-'}ms</td>
                  <td className="table-cell pr-6">{l.total_tokens || 0}</td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr><td colSpan={8} className="text-center py-12 text-gray-400">
                  <p className="text-4xl mb-3">📋</p>
                  <p>{search ? 'No logs match your search.' : 'No logs recorded yet. Make some API calls first.'}</p>
                </td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
