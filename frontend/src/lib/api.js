// Thin fetch wrapper. Same-origin (/api is proxied by Vite), cookie-based session.
export class ApiError extends Error {
  constructor(status, code, message, details) {
    super(message)
    this.status = status
    this.code = code
    this.details = details
  }
  // "amount: Input should be greater than 0" style lines for forms
  get fieldErrors() {
    const out = {}
    for (const d of this.details || []) if (d.field) out[d.field] = d.message
    return out
  }
}

const listeners = new Set()
export const onUnauthorized = (fn) => (listeners.add(fn), () => listeners.delete(fn))

export async function api(path, { method = 'GET', body, signal } = {}) {
  const res = await fetch(`/api/v1${path}`, {
    method,
    signal,
    credentials: 'same-origin',
    headers: body !== undefined ? { 'content-type': 'application/json' } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  if (res.status === 204) return null
  let data = null
  try {
    data = await res.json()
  } catch {
    /* non-JSON (e.g. proxy error) */
  }
  if (!res.ok) {
    const err = data?.error || {}
    if (res.status === 401 && !path.startsWith('/auth/')) listeners.forEach((fn) => fn())
    const fallback = res.status >= 500 ? 'The server could not complete the request.' : `Request failed (${res.status})`
    throw new ApiError(res.status, err.code || 'error', err.message || fallback, err.details)
  }
  return data
}

export const get = (p, o) => api(p, o)
export const post = (p, body) => api(p, { method: 'POST', body })
export const patch = (p, body) => api(p, { method: 'PATCH', body })
export const del = (p) => api(p, { method: 'DELETE' })
