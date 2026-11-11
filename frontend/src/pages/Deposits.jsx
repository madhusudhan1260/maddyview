import { useEffect, useState } from 'react'
import { AlertTriangle, Landmark, Pencil, Plus, Trash2 } from 'lucide-react'
import { useApi, useDebounced } from '../lib/hooks'
import { del, patch, post } from '../lib/api'
import { useApp } from '../context/AppContext'
import { dateFmt, money, pct, titleCase, todayIso } from '../lib/format'
import { Badge, Button, Card, EmptyState, ErrorNote, Loading, PageHeader, SourceBadge, Stat, Table, enumOptions } from '../components/ui'
import { ConfirmDialog, FormModal } from '../components/FormModal'

const COMPOUNDING = ['QUARTERLY', 'MONTHLY', 'HALF_YEARLY', 'YEARLY', 'SIMPLE']
const PAYOUT = ['CUMULATIVE', 'MONTHLY_PAYOUT', 'QUARTERLY_PAYOUT', 'HALF_YEARLY_PAYOUT', 'YEARLY_PAYOUT']
const STATUS = ['ACTIVE', 'MATURED', 'CLOSED', 'RENEWED']

const RATE_HELP = 'Enter the rate printed on your deposit receipt. MaddyView does not look up or guess bank rates.'

const fdFields = [
  { name: 'bank_name', label: 'Bank', required: true },
  { name: 'principal', label: 'Principal (₹)', type: 'number', step: '0.01', min: '0.01', required: true, half: true },
  { name: 'interest_rate', label: 'Interest rate (% p.a.)', type: 'number', step: '0.0001', min: '0', max: '30', required: true, half: true, help: RATE_HELP },
  { name: 'start_date', label: 'Start date', type: 'date', required: true, half: true, default: todayIso() },
  { name: 'maturity_date', label: 'Maturity date', type: 'date', required: true, half: true },
  { name: 'compounding_frequency', label: 'Compounding', type: 'select', required: true, half: true, options: enumOptions(COMPOUNDING), default: 'QUARTERLY' },
  { name: 'payout_type', label: 'Interest payout', type: 'select', required: true, half: true, options: enumOptions(PAYOUT), default: 'CUMULATIVE' },
  { name: 'tenure_months', label: 'Tenure (months, optional)', type: 'number', integer: true, min: '1', half: true, nullable: true, help: 'Informational; the dates are used for calculation.' },
  { name: 'status', label: 'Status', type: 'select', required: true, half: true, options: enumOptions(STATUS), default: 'ACTIVE' },
  { name: 'rate_verified', label: 'I have checked this rate against the bank document', type: 'checkbox' },
  { name: 'nominee_notes', label: 'Nominee notes (optional)', type: 'textarea', nullable: true },
]

const rdFields = [
  { name: 'bank_name', label: 'Bank', required: true },
  { name: 'monthly_installment', label: 'Monthly instalment (₹)', type: 'number', step: '0.01', min: '0.01', required: true, half: true },
  { name: 'interest_rate', label: 'Interest rate (% p.a.)', type: 'number', step: '0.0001', min: '0', max: '30', required: true, half: true, help: RATE_HELP },
  { name: 'start_date', label: 'Start date', type: 'date', required: true, half: true, default: todayIso() },
  { name: 'tenure_months', label: 'Tenure (months)', type: 'number', integer: true, min: '1', required: true, half: true, help: 'Maturity date = start + tenure.' },
  { name: 'compounding_frequency', label: 'Compounding', type: 'select', required: true, half: true, options: enumOptions(COMPOUNDING), default: 'QUARTERLY' },
  { name: 'status', label: 'Status', type: 'select', required: true, half: true, options: enumOptions(STATUS), default: 'ACTIVE' },
  { name: 'rate_verified', label: 'I have checked this rate against the bank document', type: 'checkbox' },
]

export default function Deposits() {
  const fds = useApi('/fixed-deposits')
  const rds = useApi('/recurring-deposits')
  const summary = useApi('/deposits/summary')
  const { settings } = useApp()
  const [editing, setEditing] = useState(null) // { kind: 'FD'|'RD', record }
  const [deleting, setDeleting] = useState(null)
  const [draft, setDraft] = useState({})
  const reloadAll = () => [fds, rds, summary].forEach((r) => r.reload())

  async function save(values) {
    const base = editing.kind === 'FD' ? '/fixed-deposits' : '/recurring-deposits'
    if (editing.record) await patch(`${base}/${editing.record.id}`, values)
    else await post(base, values)
    reloadAll()
  }

  const s = summary.data
  const rateCell = (r) => (
    <span className="inline-flex items-center gap-1.5">
      {pct(r.interest_rate)}
      {!r.rate_verified && <Badge tone="warn" title="Rate not yet checked against the bank document">Unverified</Badge>}
    </span>
  )
  const actions = (kind) => (r) => (
    <div className="flex justify-end gap-1">
      <Button size="icon" variant="ghost" aria-label="Edit" onClick={() => setEditing({ kind, record: r })}><Pencil className="size-3.5" /></Button>
      <Button size="icon" variant="ghost" aria-label="Delete" onClick={() => setDeleting({ kind, record: r })}><Trash2 className="size-3.5" /></Button>
    </div>
  )

  return (
    <div className="fade-in">
      <PageHeader
        title="Fixed & Recurring Deposits"
        description="Maturity values are calculated from the terms you enter. Gross values are shown separately from estimated post-tax values."
        actions={
          <>
            <Button icon={Plus} onClick={() => setEditing({ kind: 'RD', record: null })}>Add RD</Button>
            <Button variant="primary" icon={Plus} onClick={() => setEditing({ kind: 'FD', record: null })}>Add FD</Button>
          </>
        }
      />

      {s && (
        <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
          <Stat label="Current value" value={money(s.current_value)} hint={`${s.active_fd_count} FD · ${s.active_rd_count} RD active`} />
          <Stat label="Interest earned to date" value={money(s.interest_earned_to_date)} tone={Number(s.interest_earned_to_date) ? 'text-pos' : undefined} hint="Gross, accrued or paid" />
          <Stat label="Projected maturity value" value={money(s.projected_maturity_value)} hint={`${money(s.projected_total_interest)} total interest`} />
          <Stat
            label="Est. tax on interest"
            value={s.estimated_tax_on_projected_interest ? money(s.estimated_tax_on_projected_interest) : '—'}
            hint={settings?.tax_slab_percent ? `Estimate at ${pct(settings.tax_slab_percent, 0)} slab` : 'Set tax slab in Settings'}
            badge={<Badge>Estimate</Badge>}
          />
        </div>
      )}
      {s?.unverified_rate_count > 0 && (
        <p className="mt-3 flex items-center gap-2 text-xs text-warn">
          <AlertTriangle className="size-3.5" /> {s.unverified_rate_count} deposit(s) use a rate you have not marked as verified.
        </p>
      )}

      <Card className="mt-5" title="Fixed deposits">
        <ErrorNote error={fds.error} onRetry={fds.reload} />
        {fds.loading && !fds.data ? <Loading /> : (
          <Table
            testId="fd-table"
            rows={fds.data}
            empty={<EmptyState icon={Landmark} title="No fixed deposits" action={<Button size="sm" icon={Plus} onClick={() => setEditing({ kind: 'FD', record: null })}>Add FD</Button>}>Add an FD with the terms from your bank receipt to track its maturity.</EmptyState>}
            columns={[
              { key: 'bank_name', label: 'Bank', render: (r) => <div className="flex items-center gap-2"><span>{r.bank_name}</span>{r.source !== 'USER_ENTERED' && <SourceBadge source={r.source} />}</div> },
              { key: 'principal', label: 'Principal', align: 'right', render: (r) => money(r.principal) },
              { key: 'interest_rate', label: 'Rate', render: rateCell },
              { key: 'terms', label: 'Terms', render: (r) => <span className="text-xs text-muted">{titleCase(r.payout_type)} · {titleCase(r.compounding_frequency)}</span> },
              { key: 'maturity_date', label: 'Matures', render: (r) => <span className="whitespace-nowrap">{dateFmt(r.maturity_date)}<span className="block text-xs text-faint">{r.status === 'ACTIVE' ? (r.days_to_maturity >= 0 ? `${r.days_to_maturity} days` : 'past maturity') : titleCase(r.status)}</span></span> },
              { key: 'gross', label: 'Gross at maturity', align: 'right', render: (r) => <span>{money(r.calculation.gross_maturity_value)}<span className="block text-xs text-pos">+{money(r.calculation.total_interest)}</span></span> },
              { key: 'post_tax', label: 'Est. post-tax', align: 'right', render: (r) => <span className="text-muted">{r.calculation.tax.estimated_post_tax_value ? money(r.calculation.tax.estimated_post_tax_value) : '—'}</span> },
              { key: 'a', label: '', align: 'right', render: actions('FD') },
            ]}
          />
        )}
      </Card>

      <Card className="mt-5" title="Recurring deposits">
        <ErrorNote error={rds.error} onRetry={rds.reload} />
        {rds.loading && !rds.data ? <Loading /> : (
          <Table
            testId="rd-table"
            rows={rds.data}
            empty={<EmptyState icon={Landmark} title="No recurring deposits" action={<Button size="sm" icon={Plus} onClick={() => setEditing({ kind: 'RD', record: null })}>Add RD</Button>}>Track monthly instalments and the projected maturity value.</EmptyState>}
            columns={[
              { key: 'bank_name', label: 'Bank', render: (r) => <div className="flex items-center gap-2"><span>{r.bank_name}</span>{r.source !== 'USER_ENTERED' && <SourceBadge source={r.source} />}</div> },
              { key: 'monthly_installment', label: 'Monthly', align: 'right', render: (r) => money(r.monthly_installment) },
              { key: 'interest_rate', label: 'Rate', render: rateCell },
              { key: 'tenure', label: 'Tenure', render: (r) => <span className="text-muted">{r.tenure_months} mo · {titleCase(r.compounding_frequency)}</span> },
              { key: 'deposited', label: 'Deposited so far', align: 'right', render: (r) => money(r.deposited_to_date) },
              { key: 'maturity_date', label: 'Matures', render: (r) => <span className="whitespace-nowrap">{dateFmt(r.maturity_date)}</span> },
              { key: 'gross', label: 'Gross at maturity', align: 'right', render: (r) => <span>{money(r.calculation.gross_maturity_value)}<span className="block text-xs text-pos">+{money(r.calculation.total_interest)}</span></span> },
              { key: 'a', label: '', align: 'right', render: actions('RD') },
            ]}
          />
        )}
      </Card>

      <p className="mt-4 text-xs leading-relaxed text-faint">
        Calculation conventions: FD compounding on whole periods with simple interest (actual/365) for a broken period; payout FDs pay simple interest each period.
        RD instalments compound for the time each is held. Banks differ in their exact rules — always treat your bank's statement as authoritative.
        Tax is a rough estimate (interest × your slab) and ignores TDS thresholds, surcharge, cess and exemptions.
      </p>

      <FormModal
        open={!!editing}
        title={`${editing?.record ? 'Edit' : 'Add'} ${editing?.kind === 'FD' ? 'fixed deposit' : 'recurring deposit'}`}
        fields={editing?.kind === 'FD' ? fdFields : rdFields}
        initial={editing?.record}
        onClose={() => setEditing(null)}
        onSubmit={save}
        onChange={setDraft}
        aside={editing && <CalcPreview kind={editing.kind} values={draft} />}
      />
      <ConfirmDialog
        open={!!deleting}
        title={`Delete ${deleting?.kind}?`}
        message={deleting && `${deleting.record.bank_name} deposit will be permanently removed.`}
        onCancel={() => setDeleting(null)}
        onConfirm={async () => {
          await del(`${deleting.kind === 'FD' ? '/fixed-deposits' : '/recurring-deposits'}/${deleting.record.id}`)
          setDeleting(null)
          reloadAll()
        }}
      />
    </div>
  )
}

function CalcPreview({ kind, values }) {
  const v = useDebounced(values, 400)
  const [res, setRes] = useState(null)
  const [err, setErr] = useState(null)
  useEffect(() => {
    let cancelled = false
    const body =
      kind === 'FD'
        ? { principal: v.principal, interest_rate: v.interest_rate, start_date: v.start_date, maturity_date: v.maturity_date, compounding_frequency: v.compounding_frequency, payout_type: v.payout_type }
        : { monthly_installment: v.monthly_installment, interest_rate: v.interest_rate, tenure_months: Number(v.tenure_months), compounding_frequency: v.compounding_frequency }
    if (Object.values(body).some((x) => x === '' || x === undefined || x === null || Number.isNaN(x))) {
      setRes(null)
      setErr(null)
      return
    }
    post(kind === 'FD' ? '/fixed-deposits/calculate' : '/recurring-deposits/calculate', body)
      .then((r) => !cancelled && (setRes(r), setErr(null)))
      .catch((e) => !cancelled && (setRes(null), setErr(e)))
    return () => (cancelled = true)
  }, [kind, v])

  return (
    <div className="rounded-xl border border-line bg-surface-2 p-3 text-sm" data-testid="calc-preview">
      <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">Calculation preview</div>
      {!res && !err && <p className="text-xs text-faint">Fill in the amount, rate and dates to see the maturity value.</p>}
      {err && <p className="text-xs text-neg">{Object.values(err.fieldErrors || {})[0] || err.message}</p>}
      {res && (
        <dl className="space-y-1.5">
          <Row k={kind === 'FD' ? 'Principal' : 'Total deposited'} v={money(kind === 'FD' ? res.principal : res.total_deposited)} />
          <Row k="Total interest (gross)" v={<span className="text-pos">{money(res.total_interest)}</span>} />
          <Row k="Gross maturity value" v={<b>{money(res.gross_maturity_value)}</b>} />
          {res.periodic_payout && <Row k={`Payout × ${res.payout_count}`} v={money(res.periodic_payout)} />}
          <div className="my-2 border-t border-line" />
          <Row k="Est. tax" v={res.tax.estimated_tax ? money(res.tax.estimated_tax) : '—'} />
          <Row k="Est. post-tax value" v={res.tax.estimated_post_tax_value ? money(res.tax.estimated_post_tax_value) : '—'} />
          <p className="pt-1 text-[11px] leading-snug text-faint">{res.tax.note}</p>
          <p className="text-[11px] leading-snug text-faint">{res.method}</p>
        </dl>
      )}
    </div>
  )
}

const Row = ({ k, v }) => (
  <div className="flex justify-between gap-3">
    <dt className="text-xs text-muted">{k}</dt>
    <dd className="num text-right text-sm">{v}</dd>
  </div>
)
