import { useState, useEffect } from 'react'
import { apiGet } from '../api'

export default function Health() {
  const [providerHealth, setProviderHealth] = useState<any[]>([])
  const [overall, setOverall] = useState<any>(null)

  useEffect(() => {
    apiGet('/health/providers').then(setProviderHealth).catch(() => {})
    apiGet('/health').then(setOverall).catch(() => {})
  }, [])

  const healthy = providerHealth.filter(h => h.status === 'healthy').length
  const degraded = providerHealth.filter(h => h.status === 'degraded').length
  const unhealthy = providerHealth.filter(h => h.status === 'unhealthy').length
  const statusOverall = unhealthy > 0 ? 'degraded' : 'healthy'

  return (
    <div className="animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold dark:text-white">Health</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Provider health monitoring</p>
      </div>
      <div className={`card p-5 mb-6 ${statusOverall === 'healthy' ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800' : 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800'}`}>
        <div className="flex items-center gap-3">
          <span className={`w-3 h-3 rounded-full ${statusOverall === 'healthy' ? 'bg-green-500' : 'bg-yellow-500'}`} />
          <span className="font-semibold dark:text-white">{statusOverall.toUpperCase()}</span>
          {overall && <span className="text-sm text-gray-500">Uptime: {Math.floor(overall.uptime_seconds / 60)}m {Math.floor(overall.uptime_seconds % 60)}s</span>}
        </div>
      </div>
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="stat-card text-center"><div className="stat-value text-green-600">{healthy}</div><div className="stat-label">Healthy</div></div>
        <div className="stat-card text-center"><div className="stat-value text-yellow-600">{degraded}</div><div className="stat-label">Degraded</div></div>
        <div className="stat-card text-center"><div className={`stat-value ${unhealthy > 0 ? 'text-red-600' : 'text-gray-500'}`}>{unhealthy}</div><div className="stat-label">Unhealthy</div></div>
      </div>
      <div className="card">
        <div className="card-header">Provider Status</div>
        <div className="p-4 grid gap-3">
          {providerHealth.map(h => (
            <div key={h.name} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/30 rounded-lg">
              <div className="flex items-center gap-3">
                <span className={`w-2.5 h-2.5 rounded-full ${h.status === 'healthy' ? 'bg-green-500' : h.status === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'}`} />
                <span className="font-medium dark:text-white">{h.name}</span>
                <span className={`badge ${h.status === 'healthy' ? 'badge-green' : h.status === 'degraded' ? 'badge-yellow' : 'badge-red'}`}>{h.status}</span>
              </div>
              <div className="flex gap-4 text-sm text-gray-500">
                <span>⚡ {h.avg_latency_ms?.toFixed(0) || '-'}ms</span>
                <span>❌ {h.consecutive_failures} failures</span>
                <span>🕐 {h.last_check ? new Date(h.last_check).toLocaleTimeString() : '-'}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
