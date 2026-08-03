import { useState, useEffect } from 'react'
import { apiGet } from '../api'

export default function Usage() {
  const [stats, setStats] = useState<any>(null)
  useEffect(() => { apiGet('/admin/stats').then(setStats).catch(() => {}) }, [])

  if (!stats) return <div className="flex justify-center py-12"><svg className="animate-spin h-8 w-8 text-blue-500" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg></div>

  const cards = [
    { label: 'Total Requests', value: stats.total_requests, icon: '📨' },
    { label: 'Errors', value: stats.total_errors, icon: '❌' },
    { label: 'Total Tokens', value: stats.total_tokens?.toLocaleString(), icon: '🔤' },
    { label: 'Avg Latency', value: stats.avg_latency_ms ? `${stats.avg_latency_ms.toFixed(0)}ms` : '0ms', icon: '⚡' },
    { label: 'Estimated Cost', value: `$${(stats.estimated_cost_usd || 0).toFixed(4)}`, icon: '💰' },
  ]

  return (
    <div className="animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold dark:text-white">Usage</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Gateway usage statistics</p>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
        {cards.map(c => (
          <div key={c.label} className="stat-card text-center">
            <div className="text-2xl mb-1">{c.icon}</div>
            <div className="stat-value dark:text-white">{c.value}</div>
            <div className="stat-label">{c.label}</div>
          </div>
        ))}
      </div>
      {stats.by_provider && (
        <div className="card">
          <div className="card-header">By Provider</div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 dark:border-gray-700">
                  <th className="table-header pl-6">Provider</th><th className="table-header">Requests</th><th className="table-header">Errors</th><th className="table-header">Tokens</th><th className="table-header pr-6">Cost</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(stats.by_provider).map(([k, v]: [string, any]) => (
                  <tr key={k}>
                    <td className="table-cell pl-6 font-medium dark:text-white">{k}</td>
                    <td className="table-cell">{v.requests}</td>
                    <td className="table-cell text-red-500">{v.errors}</td>
                    <td className="table-cell">{v.tokens?.toLocaleString()}</td>
                    <td className="table-cell pr-6">${(v.cost || 0).toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
