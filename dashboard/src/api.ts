const BASE = window.location.origin

function getToken() { return localStorage.getItem('gateway_token') || '' }
export function setToken(t: string) { localStorage.setItem('gateway_token', t) }
export function getAuthHeaders() { const t = getToken(); return t ? { Authorization: `Bearer ${t}` } : {} }

export async function apiGet(path: string) {
  const r = await fetch(BASE + path, { headers: { ...getAuthHeaders(), Accept: 'application/json' } })
  if (r.status === 401) { localStorage.removeItem('gateway_token'); throw new Error('Unauthorized') }
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function apiPost(path: string, body?: any) {
  const r = await fetch(BASE + path, {
    method: 'POST', headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined
  })
  if (!r.ok) { const e = await r.text(); throw new Error(e) }
  return r.json()
}

export async function apiPut(path: string, body?: any) {
  const r = await fetch(BASE + path, {
    method: 'PUT', headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined
  })
  if (!r.ok) { const e = await r.text(); throw new Error(e) }
  return r.json()
}

export async function apiDelete(path: string) {
  const r = await fetch(BASE + path, { method: 'DELETE', headers: getAuthHeaders() })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}
