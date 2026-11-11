import { useState } from 'react'
import { BarChart3, Lock, ShieldCheck } from 'lucide-react'
import { post } from '../lib/api'
import { useApp } from '../context/AppContext'
import { Button } from '../components/ui'

const inputCls =
  'h-10 w-full rounded-lg border border-line bg-surface-2 px-3 text-sm text-fg placeholder:text-faint focus:border-accent focus:outline-none focus:ring-2 focus:ring-[var(--ring)]'

export default function AuthPage({ setup }) {
  const { refreshAuth } = useApp()
  const [form, setForm] = useState({ email: '', display_name: '', password: '', confirm: '' })
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  async function submit(e) {
    e.preventDefault()
    setError(null)
    if (setup && form.password !== form.confirm) return setError('Passwords do not match.')
    setBusy(true)
    try {
      if (setup) await post('/auth/register', { email: form.email, display_name: form.display_name, password: form.password })
      else await post('/auth/login', { email: form.email, password: form.password })
      await refreshAuth()
    } catch (err) {
      const fe = err.fieldErrors || {}
      setError(Object.keys(fe).length ? Object.entries(fe).map(([k, v]) => `${k.replace('_', ' ')}: ${v}`).join(' · ') : err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="grid min-h-screen place-items-center px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex items-center gap-3">
          <div className="grid size-10 place-items-center rounded-xl border border-line bg-surface">
            <BarChart3 className="size-5 text-pos" />
          </div>
          <div>
            <h1 className="text-lg font-semibold tracking-tight">MaddyView</h1>
            <p className="text-xs text-muted">Personal financial intelligence</p>
          </div>
        </div>
        <form onSubmit={submit} className="rounded-xl border border-line bg-surface p-5" noValidate>
          <h2 className="text-sm font-semibold">{setup ? 'Create your account' : 'Sign in'}</h2>
          <p className="mt-1 text-xs text-muted">
            {setup ? 'MaddyView is single-user. This account becomes the only login.' : 'Welcome back.'}
          </p>
          <div className="mt-4 space-y-3">
            {setup && (
              <label className="block text-xs font-medium text-muted">
                Name
                <input className={`${inputCls} mt-1`} value={form.display_name} onChange={set('display_name')} autoComplete="name" required />
              </label>
            )}
            <label className="block text-xs font-medium text-muted">
              Email
              <input className={`${inputCls} mt-1`} type="email" value={form.email} onChange={set('email')} autoComplete="email" required />
            </label>
            <label className="block text-xs font-medium text-muted">
              Password
              <input
                className={`${inputCls} mt-1`}
                type="password"
                value={form.password}
                onChange={set('password')}
                autoComplete={setup ? 'new-password' : 'current-password'}
                required
              />
            </label>
            {setup && (
              <>
                <label className="block text-xs font-medium text-muted">
                  Confirm password
                  <input className={`${inputCls} mt-1`} type="password" value={form.confirm} onChange={set('confirm')} autoComplete="new-password" required />
                </label>
                <p className="text-xs text-faint">At least 12 characters, using 3 of: lowercase, uppercase, digit, symbol.</p>
              </>
            )}
          </div>
          {error && (
            <p className="mt-3 rounded-lg border border-neg/30 bg-neg/10 px-3 py-2 text-xs text-neg" role="alert">
              {error}
            </p>
          )}
          <Button variant="primary" type="submit" className="mt-4 w-full justify-center" loading={busy} icon={Lock}>
            {setup ? 'Create account' : 'Sign in'}
          </Button>
        </form>
        <p className="mt-4 flex items-center gap-1.5 text-xs text-faint">
          <ShieldCheck className="size-3.5" /> Argon2id password hashing · HttpOnly session cookie · no real-money trading
        </p>
      </div>
    </div>
  )
}
