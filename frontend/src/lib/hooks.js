import { useCallback, useEffect, useRef, useState } from 'react'
import { get } from './api'
import { useApp } from '../context/AppContext'

// Fetch a GET endpoint; re-runs when `path` changes. `reload()` refetches.
export function useApi(path) {
  const [state, setState] = useState({ data: null, error: null, loading: !!path })
  const [nonce, setNonce] = useState(0)
  const dataVersion = useApp()?.dataVersion ?? 0
  useEffect(() => {
    if (!path) return
    const ctrl = new AbortController()
    setState((s) => ({ ...s, loading: true, error: null }))
    get(path, { signal: ctrl.signal })
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((error) => {
        if (error.name !== 'AbortError') setState({ data: null, error, loading: false })
      })
    return () => ctrl.abort()
  }, [path, nonce, dataVersion])
  const reload = useCallback(() => setNonce((n) => n + 1), [])
  return { ...state, reload }
}

export function useDebounced(value, ms = 350) {
  const [v, setV] = useState(value)
  const t = useRef()
  useEffect(() => {
    clearTimeout(t.current)
    t.current = setTimeout(() => setV(value), ms)
    return () => clearTimeout(t.current)
  }, [value, ms])
  return v
}
