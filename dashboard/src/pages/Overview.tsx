import { useState, useEffect } from 'react'
import { apiGet } from '../api'
import { Link } from 'react-router-dom'

export default function Overview() {
  const [stats, setStats] = useState<any>(null)
  const [health, setHealth] = useState<any>(null)
  const [providers, setProviders] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      apiGet('/admin/stats').catch(() => null),
      apiGet('/health').catch(() => null),
      apiGet('/admin/providers').catch(() => []),
    ]).then(([s, h, p]) => {
      setStats(s)
      setHealth(h)
      setProviders(p || [])
      setLoading(false)
    })
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <svg className="animate-spin h-8 w-8 text-blue-500" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>
  )

  const enabled = providers.filter(p => p.enabled).length
  const healthy = providers.filter(p => p.status === 'healthy').length
  const unhealthy = providers.filter(p => p.status === 'unhealthy').length

  const cards = [
    { label: 'Total Requests', value: stats?.total_requests ?? 0, icon: '📨', color: 'text-blue-600' },
    { label: 'Total Tokens', value: (stats?.total_tokens ?? 0).toLocaleString(), icon: '🔤', color: 'text-purple-600' },
    { label: 'Avg Latency', value: stats?.avg_latency_ms ? `${stats.avg_latency_ms.toFixed(0)}ms` : '0ms', icon: '⚡', color: 'text-yellow-600' },
    { label: 'Cost (est.)', value: `$${(stats?.estimated_cost_usd ?? 0).toFixed(4)}`, icon: '💰', color: 'text-green-600' },
    { label: 'Errors', value: stats?.total_errors ?? 0, icon: '❌', color: 'text-red-600' },
    { label: 'Uptime', value: health?.uptime_seconds ? `${Math.floor(health.uptime_seconds / 60)}m` : 'N/A', icon: '⏱️', color: 'text-gray-600' },
  ]

  return (
    <div className="animate-fade-in">
      <div className="mb-8">
        <h1 className="text-2xl font-bold dark:text-white">Dashboard</h1>
        <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">Mini LiteLLM Gateway — v1.0.0</p>
      </div>

      {/* Status Banner */}
      <div className={`card p-4 mb-6 flex items-center gap-3 ${unhealthy > 0 ? 'border-yellow-300 dark:border-yellow-700 bg-yellow-50 dark:bg-yellow-900/20' : 'border-green-300 dark:border-green-700 bg-green-50 dark:bg-green-900/20'}`}>
        <span className={`w-3 h-3 rounded-full ${unhealthy > 0 ? 'bg-yellow-500' : 'bg-green-500'}`} />
        <span className="font-medium text-sm dark:text-white">
          {unhealthy > 0
            ? `${unhealthy} provider(s) unhealthy — check Health page`
            : 'All systems operational'
          }
        </span>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        {cards.map(c => (
          <div key={c.label} className="stat-card">
            <div className="flex items-center gap-2">
              <span className="text-xl">{c.icon}</span>
              <span className="stat-label">{c.label}</span>
            </div>
            <div className={`stat-value ${c.color} dark:text-white`}>{c.value}</div>
          </div>
        ))}
      </div>

      {/* Provider Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="card">
          <div className="card-header">Provider Status</div>
          <div className="card-body">
            <div className="flex gap-4 mb-4">
              <div className="text-center flex-1 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{providers.length}</div>
                <div className="text-xs text-gray-500 mt-1">Total</div>
              </div>
              <div className="text-center flex-1 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{enabled}</div>
                <div className="text-xs text-gray-500 mt-1">Enabled</div>
              </div>
              <div className="text-center flex-1 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{healthy}</div>
                <div className="text-xs text-gray-500 mt-1">Healthy</div>
              </div>
              <div className={`text-center flex-1 p-3 rounded-lg ${unhealthy > 0 ? 'bg-red-50 dark:bg-red-900/20' : 'bg-gray-50 dark:bg-gray-700/50'}`}>
                <div className={`text-2xl font-bold ${unhealthy > 0 ? 'text-red-600' : 'text-gray-500'}`}>{unhealthy}</div>
                <div className="text-xs text-gray-500 mt-1">Unhealthy</div>
              </div>
            </div>
            <Link to="/providers" className="btn-secondary text-sm w-full justify-center">Manage Providers →</Link>
          </div>
        </div>

        <div className="card">
          <div className="card-header">Quick Actions</div>
          <div className="card-body space-y-2">
            <Link to="/models" className="btn-secondary w-full justify-start">🔍 View Models</Link>
            <Link to="/keys" className="btn-secondary w-full justify-start">🔑 Manage API Keys</Link>
            <Link to="/config" className="btn-secondary w-full justify-start">📝 Edit Configuration</Link>
            <Link to="/logs" className="btn-secondary w-full justify-start">📋 View Request Logs</Link>
          </div>
        </div>
      </div>

      {/* Recent Providers */}
      <div className="card">
        <div className="card-header flex items-center justify-between">
          <span>Providers Overview</span>
          <Link to="/providers" className="text-xs text-blue-600 hover:underline">View All</Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 dark:border-gray-700">
                <th className="table-header pl-6">Provider</th>
                <th className="table-header">Type</th>
                <th className="table-header">Status</th>
                <th className="table-header">Keys</th>
                <th className="table-header pr-6">Latency</th>
              </tr>
            </thead>
            <tbody>
              {providers.slice(0, 6).map(p => (
                <tr key={p.name}>
                  <td className="table-cell pl-6 font-medium dark:text-white">{p.name}</td>
                  <td className="table-cell text-gray-500">{p.type}</td>
                  <td className="table-cell">
                    <span className={`badge ${
                      p.status === 'healthy' ? 'badge-green' :
                      p.status === 'degraded' ? 'badge-yellow' : 'badge-red'
                    }`}>{p.status}</span>
                  </td>
                  <td className="table-cell">{p.api_keys_count}</td>
                  <td className="table-cell pr-6">{p.avg_latency_ms?.toFixed(0) || '-'}ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
