import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { get, onUnauthorized, patch, post } from '../lib/api'

const AppCtx = createContext(null)

export function AppProvider({ children }) {
  const [auth, setAuth] = useState({ loading: true, setupRequired: false, user: null, error: null })
  const [settings, setSettings] = useState(null)
  const [theme, setThemeState] = useState(() => document.documentElement.dataset.theme || 'dark')
  // Bumped whenever data that many pages show changes (e.g. DEMO toggle) so they refetch.
  const [dataVersion, setDataVersion] = useState(0)

  const applyTheme = useCallback((t) => {
    document.documentElement.dataset.theme = t
    try {
      localStorage.setItem('finpilot-theme', t)
    } catch {
      /* storage unavailable */
    }
    setThemeState(t)
  }, [])

  const refreshAuth = useCallback(async () => {
    try {
      const s = await get('/auth/status')
      setAuth({ loading: false, setupRequired: s.setup_required, user: s.user, error: null })
      if (s.user) {
        const st = await get('/settings')
        setSettings(st)
        applyTheme(st.theme === 'LIGHT' ? 'light' : 'dark')
      }
    } catch (e) {
      setAuth({ loading: false, setupRequired: false, user: null, error: e })
    }
  }, [applyTheme])

  useEffect(() => {
    refreshAuth()
    return onUnauthorized(() => setAuth((a) => ({ ...a, user: null })))
  }, [refreshAuth])

  const updateSettings = useCallback(async (changes) => {
    const st = await patch('/settings', changes)
    setSettings(st)
    if ('include_demo_data' in changes || 'tax_slab_percent' in changes) setDataVersion((v) => v + 1)
    return st
  }, [])

  const setTheme = useCallback(
    (t) => {
      applyTheme(t)
      if (auth.user) updateSettings({ theme: t === 'light' ? 'LIGHT' : 'DARK' }).catch(() => {})
    },
    [applyTheme, auth.user, updateSettings],
  )

  const logout = useCallback(async () => {
    await post('/auth/logout').catch(() => {})
    setAuth((a) => ({ ...a, user: null }))
    setSettings(null)
  }, [])

  const value = useMemo(
    () => ({
      auth, settings, theme, setTheme, refreshAuth, updateSettings, logout, dataVersion,
      bumpData: () => setDataVersion((v) => v + 1),
      reloadSettings: async () => setSettings(await get('/settings')),
    }),
    [auth, settings, theme, setTheme, refreshAuth, updateSettings, logout, dataVersion],
  )
  return <AppCtx.Provider value={value}>{children}</AppCtx.Provider>
}

export const useApp = () => useContext(AppCtx)
