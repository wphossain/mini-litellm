const BASE = window.location.origin

function getToken() { return localStorage.getItem('gateway_token') || '' }
export function setToken(t: string) { localStorage.setItem('gateway_token', t) }
export function clearToken() { localStorage.removeItem('gateway_token') }
export function getAuthHeaders() { const t = getToken(); return t ? { Authorization: `Bearer ${t}` } : {} }

type ToastFn = (msg: string, type?: 'success' | 'error' | 'info') => void
let _toast: ToastFn = () => {}
export function setToastFn(fn: ToastFn) { _toast = fn }

async function handleResponse(r: Response) {
  if (r.status === 401) {
    clearToken()
    _toast('Session expired. Please login again.', 'error')
    window.location.reload()
    throw new Error('Unauthorized')
  }
  if (!r.ok) {
    const text = await r.text()
    _toast(text.slice(0, 200), 'error')
    throw new Error(text)
  }
  return r.json()
}

export async function apiGet(path: string) {
  const r = await fetch(BASE + path, { headers: { ...getAuthHeaders(), Accept: 'application/json' } })
  return handleResponse(r)
}

export async function apiPost(path: string, body?: any) {
  const r = await fetch(BASE + path, {
    method: 'POST',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  return handleResponse(r)
}

export async function apiPut(path: string, body?: any) {
  const r = await fetch(BASE + path, {
    method: 'PUT',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  return handleResponse(r)
}

export async function apiDelete(path: string) {
  const r = await fetch(BASE + path, { method: 'DELETE', headers: getAuthHeaders() })
  return handleResponse(r)
}
