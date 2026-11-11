import { useEffect, useState } from 'react'
import { Database, FlaskConical, Moon, Shield, Sun } from 'lucide-react'
import { useApp } from '../context/AppContext'
import { useApi } from '../lib/hooks'
import { del, post } from '../lib/api'
import { dateFmt } from '../lib/format'
import { Button, Card, ErrorNote, Loading, PageHeader, Segmented, SourceBadge } from '../components/ui'

export default function SettingsPage() {
  const { settings, updateSettings, theme, setTheme, reloadSettings, bumpData, logout } = useApp()
  const labels = useApi('/data-sources/labels')
  const demo = useApi('/demo')
  const audit = useApi('/audit-logs?limit=15')
  const [slab, setSlab] = useState('')
  const [msg, setMsg] = useState(null)
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(null)

  useEffect(() => setSlab(settings?.tax_slab_percent ?? ''), [settings?.tax_slab_percent])
  if (!settings) return <Loading />

  const run = (key, fn) => async () => {
    setBusy(key)
    setErr(null)
    setMsg(null)
    try {
      const r = await fn()
      if (r?.message) setMsg(r.message)
      await reloadSettings()
      bumpData()
      demo.reload()
      audit.reload()
    } catch (e) {
      setErr(e)
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="fade-in max-w-3xl">
      <PageHeader title="Settings" />
      {msg && <p className="mb-4 rounded-lg border border-pos/30 bg-pos/10 px-3 py-2 text-sm text-pos" role="status">{msg}</p>}
      <ErrorNote error={err} />

      <Card title="Appearance" className="mb-5">
        <Segmented value={theme} onChange={setTheme} options={[{ value: 'dark', label: 'Dark' }, { value: 'light', label: 'Light' }]} />
        <p className="mt-2 flex items-center gap-1.5 text-xs text-muted">{theme === 'dark' ? <Moon className="size-3.5" /> : <Sun className="size-3.5" />} Saved to your account.</p>
      </Card>

      <Card title="Tax estimate" subtitle="Used only to estimate tax on FD/RD interest" className="mb-5">
        <div className="flex flex-wrap items-end gap-2">
          <label className="text-xs font-medium text-muted">
            Marginal income-tax slab (%)
            <input
              type="number" min="0" max="50" step="0.01" value={slab} onChange={(e) => setSlab(e.target.value)} aria-label="Tax slab percent"
              className="num mt-1 block h-9 w-40 rounded-lg border border-line bg-surface-2 px-2.5 text-sm text-fg focus:border-accent focus:outline-none"
            />
          </label>
          <Button variant="primary" loading={busy === 'slab'} onClick={run('slab', () => updateSettings({ tax_slab_percent: slab === '' ? null : String(slab) }))}>Save</Button>
          {settings.tax_slab_percent && <Button variant="ghost" onClick={run('slab', () => updateSettings({ tax_slab_percent: null }))}>Clear</Button>}
        </div>
        <p className="mt-2 text-xs text-faint">Estimates are interest × slab. They ignore TDS thresholds, surcharge, cess, 15G/15H and senior-citizen exemptions. Not tax advice.</p>
      </Card>

      <Card title="DEMO data" subtitle="Illustrative sample records for exploring the app" className="mb-5">
        <div className="flex flex-wrap items-center gap-2">
          <Button icon={FlaskConical} loading={busy === 'load'} onClick={run('load', () => post('/demo'))}>{demo.data?.has_demo_data ? 'Reload DEMO data' : 'Load DEMO data'}</Button>
          {demo.data?.has_demo_data && (
            <>
              <Button loading={busy === 'toggle'} onClick={run('toggle', () => updateSettings({ include_demo_data: !settings.include_demo_data }))}>
                {settings.include_demo_data ? 'Hide DEMO data' : 'Show DEMO data'}
              </Button>
              <Button variant="danger" loading={busy === 'clear'} onClick={run('clear', () => del('/demo'))}>Remove DEMO data</Button>
            </>
          )}
        </div>
        <p className="mt-2 text-xs text-faint">
          DEMO records use fictional names (“Demo Bank (fictional)”), unverified rates and the DEMO label. They are never mixed into totals unless shown, and a banner is displayed while they are visible.
        </p>
      </Card>

      <Card title="Data-source labels" subtitle="Every financial record carries one of these" className="mb-5">
        {labels.data ? (
          <ul className="space-y-2">
            {labels.data.map((l) => (
              <li key={l.label} className="flex items-start gap-3 text-sm">
                <SourceBadge source={l.label} className="mt-0.5 w-20 justify-center" />
                <span className="text-muted">{l.meaning}</span>
              </li>
            ))}
          </ul>
        ) : <Loading />}
      </Card>

      <Card title="Security activity" subtitle="Recent audit log entries" className="mb-5" actions={<Shield className="size-4 text-faint" />}>
        {audit.data?.length ? (
          <ul className="divide-y divide-line/60 text-xs">
            {audit.data.map((a) => (
              <li key={a.id} className="flex justify-between gap-3 py-1.5">
                <span className="font-mono">{a.action}</span>
                <span className="num text-faint">{dateFmt(a.created_at)} {new Date(a.created_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}</span>
              </li>
            ))}
          </ul>
        ) : <p className="text-xs text-muted">No activity yet.</p>}
      </Card>

      <Card title="Session">
        <div className="flex items-center justify-between gap-3">
          <p className="flex items-center gap-2 text-xs text-muted"><Database className="size-3.5" /> Data is stored in your local PostgreSQL database.</p>
          <Button variant="danger" onClick={logout}>Sign out</Button>
        </div>
      </Card>
    </div>
  )
}
