import { useState, useEffect } from 'react'
import { apiGet } from '../api'

export default function Logs() {
  const [logs, setLogs] = useState<any[]>([])
  const [total, setTotal] = useState(0)

  useEffect(() => { load() }, [])

  async function load() {
    try {
      const d = await apiGet('/admin/logs?limit=50')
      setLogs(d.logs || [])
      setTotal(d.total)
    } catch {}
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold dark:text-white">Logs ({total})</h1>
        <button onClick={load} className="btn btn-outline">Refresh</button>
      </div>
      <div className="card overflow-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-400">
              <th className="pb-3">Time</th><th className="pb-3">Method</th><th className="pb-3">Path</th><th className="pb-3">Provider</th><th className="pb-3">Model</th><th className="pb-3">Status</th><th className="pb-3">Latency</th><th className="pb-3">Tokens</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((l, i) => (
              <tr key={i} className="border-t border-gray-100 dark:border-gray-700">
                <td className="py-2 dark:text-gray-300">{new Date(l.timestamp).toLocaleTimeString()}</td>
                <td className="py-2 dark:text-gray-300">{l.method}</td>
                <td className="py-2 dark:text-gray-300">{l.path}</td>
                <td className="py-2 dark:text-gray-300">{l.provider || '-'}</td>
                <td className="py-2 dark:text-gray-300">{l.model || '-'}</td>
                <td className="py-2"><span className={`badge ${l.status_code < 400 ? 'badge-green' : 'badge-red'}`}>{l.status_code}</span></td>
                <td className="py-2 dark:text-gray-300">{l.latency_ms?.toFixed(0)}ms</td>
                <td className="py-2 dark:text-gray-300">{l.total_tokens || 0}</td>
              </tr>
            ))}
            {logs.length === 0 && <tr><td colSpan={8} className="py-8 text-center text-gray-400">No logs yet</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
