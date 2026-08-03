import { useState, useEffect } from 'react'
import { apiGet } from '../api'

export default function Usage() {
  const [stats, setStats] = useState<any>(null)
  useEffect(() => { apiGet('/admin/stats').then(setStats).catch(() => {}) }, [])

  if (!stats) return <div className="text-gray-500">Loading...</div>

  const cards = [
    { label: 'Total Requests', value: stats.total_requests },
    { label: 'Total Errors', value: stats.total_errors },
    { label: 'Total Tokens', value: stats.total_tokens?.toLocaleString() },
    { label: 'Avg Latency', value: stats.avg_latency_ms + 'ms' },
    { label: 'Cost (est)', value: '$' + (stats.estimated_cost_usd || 0).toFixed(4) },
  ]

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6 dark:text-white">Usage</h1>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
        {cards.map(c => (
          <div key={c.label} className="card text-center">
            <p className="text-2xl font-bold dark:text-white">{c.value}</p>
            <p className="text-sm text-gray-400">{c.label}</p>
          </div>
        ))}
      </div>
      {stats.by_provider && (
        <div className="card">
          <h3 className="font-semibold mb-4 dark:text-white">By Provider</h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-400"><th className="pb-2">Provider</th><th className="pb-2">Requests</th><th className="pb-2">Errors</th><th className="pb-2">Tokens</th><th className="pb-2">Cost</th></tr>
            </thead>
            <tbody>
              {Object.entries(stats.by_provider).map(([k, v]: [string, any]) => (
                <tr key={k} className="border-t border-gray-100 dark:border-gray-700">
                  <td className="py-2 font-medium dark:text-white">{k}</td>
                  <td className="py-2 dark:text-gray-300">{v.requests}</td>
                  <td className="py-2 text-red-500">{v.errors}</td>
                  <td className="py-2 dark:text-gray-300">{v.tokens?.toLocaleString()}</td>
                  <td className="py-2 dark:text-gray-300">${(v.cost || 0).toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
