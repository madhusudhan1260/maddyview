import { useState } from 'react'
import { AlertTriangle, CalendarCheck, Pencil, PiggyBank, Plus, Target, Trash2, TrendingUp } from 'lucide-react'
import { useApi } from '../lib/hooks'
import { del, patch, post } from '../lib/api'
import { dateFmt, money, pct, titleCase } from '../lib/format'
import { Badge, Button, Card, EmptyState, ErrorNote, Loading, PageHeader, Progress, SourceBadge, enumOptions } from '../components/ui'
import { ConfirmDialog, FormModal } from '../components/FormModal'

const STATUS = ['ACTIVE', 'ACHIEVED', 'PAUSED', 'CANCELLED']
const common = [
  { name: 'name', label: 'Goal name', required: true },
  { name: 'target_amount', label: 'Target amount (₹)', type: 'number', step: '0.01', min: '0.01', required: true, half: true },
  { name: 'current_amount', label: 'Saved so far (₹)', type: 'number', step: '0.01', min: '0', half: true, default: '0' },
  { name: 'monthly_contribution', label: 'Monthly contribution (₹)', type: 'number', step: '0.01', min: '0', half: true, default: '0' },
  { name: 'target_date', label: 'Target date (optional)', type: 'date', half: true, nullable: true },
  { name: 'status', label: 'Status', type: 'select', required: true, half: true, options: enumOptions(STATUS), default: 'ACTIVE' },
]
const savingsFields = [...common, { name: 'notes', label: 'Notes', type: 'textarea', nullable: true }]
const investmentFields = [
  ...common,
  { name: 'expected_annual_return_percent', label: 'Assumed annual return (%)', type: 'number', step: '0.1', min: '-50', max: '50', required: true, half: true,
    help: 'Your assumption, not a forecast. Markets can return less, or lose money.' },
  { name: 'risk_profile', label: 'Risk profile (optional)', half: true, nullable: true, list: ['Conservative', 'Moderate', 'Aggressive'] },
  { name: 'notes', label: 'Notes', type: 'textarea', nullable: true },
]

export default function Goals() {
  const sg = useApi('/savings-goals')
  const ig = useApi('/investment-goals')
  const [editing, setEditing] = useState(null) // {kind, record}
  const [deleting, setDeleting] = useState(null)
  const base = (k) => (k === 'SAVINGS' ? '/savings-goals' : '/investment-goals')

  async function save(values) {
    if (editing.record) await patch(`${base(editing.kind)}/${editing.record.id}`, values)
    else await post(base(editing.kind), values)
    ;(editing.kind === 'SAVINGS' ? sg : ig).reload()
  }

  return (
    <div className="fade-in">
      <PageHeader
        title="Financial Goals"
        description="Savings goals are projected from contributions only. Investment goals use a return you assume — they are projections, not guarantees."
        actions={
          <>
            <Button icon={TrendingUp} onClick={() => setEditing({ kind: 'INVESTMENT', record: null })}>Investment goal</Button>
            <Button variant="primary" icon={PiggyBank} onClick={() => setEditing({ kind: 'SAVINGS', record: null })}>Savings goal</Button>
          </>
        }
      />

      <Section title="Savings goals" subtitle="Deterministic: no interest or return assumed" q={sg} kind="SAVINGS"
        onEdit={(r) => setEditing({ kind: 'SAVINGS', record: r })} onDelete={(r) => setDeleting({ kind: 'SAVINGS', record: r })}
        onAdd={() => setEditing({ kind: 'SAVINGS', record: null })} />
      <Section title="Investment goals" subtitle="Projection based on your assumed return — uncertain" q={ig} kind="INVESTMENT"
        onEdit={(r) => setEditing({ kind: 'INVESTMENT', record: r })} onDelete={(r) => setDeleting({ kind: 'INVESTMENT', record: r })}
        onAdd={() => setEditing({ kind: 'INVESTMENT', record: null })} />

      <FormModal
        open={!!editing}
        title={`${editing?.record ? 'Edit' : 'New'} ${editing?.kind === 'SAVINGS' ? 'savings' : 'investment'} goal`}
        fields={editing?.kind === 'SAVINGS' ? savingsFields : investmentFields}
        initial={editing?.record}
        onClose={() => setEditing(null)}
        onSubmit={save}
      />
      <ConfirmDialog
        open={!!deleting}
        title="Delete goal?"
        message={deleting && `“${deleting.record.name}” will be permanently removed.`}
        onCancel={() => setDeleting(null)}
        onConfirm={async () => {
          await del(`${base(deleting.kind)}/${deleting.record.id}`)
          ;(deleting.kind === 'SAVINGS' ? sg : ig).reload()
          setDeleting(null)
        }}
      />
    </div>
  )
}

function Section({ title, subtitle, q, kind, onEdit, onDelete, onAdd }) {
  return (
    <Card className="mb-5" title={title} subtitle={subtitle}>
      <ErrorNote error={q.error} onRetry={q.reload} />
      {q.loading && !q.data ? <Loading /> : q.data?.length ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {q.data.map((g) => <GoalCard key={g.id} g={g} kind={kind} onEdit={() => onEdit(g)} onDelete={() => onDelete(g)} />)}
        </div>
      ) : (
        <EmptyState icon={Target} title={`No ${kind === 'SAVINGS' ? 'savings' : 'investment'} goals`} action={<Button size="sm" icon={Plus} onClick={onAdd}>Add goal</Button>}>
          {kind === 'SAVINGS' ? 'For example an emergency fund or a trip.' : 'For example retirement or a child’s education, with the annual return you are willing to assume.'}
        </EmptyState>
      )}
    </Card>
  )
}

function GoalCard({ g, kind, onEdit, onDelete }) {
  const p = g.projection
  return (
    <div className="rounded-xl border border-line bg-surface-2/50 p-4" data-testid="goal-card">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="truncate text-sm font-semibold">{g.name}</h3>
            {g.source !== 'USER_ENTERED' && <SourceBadge source={g.source} />}
          </div>
          <div className="mt-0.5 flex flex-wrap gap-1.5">
            {g.status !== 'ACTIVE' && <Badge>{titleCase(g.status)}</Badge>}
            {kind === 'INVESTMENT' && <Badge tone="warn" title={p.assumption}>Assumes {pct(g.expected_annual_return_percent, 1)} p.a.</Badge>}
          </div>
        </div>
        <div className="flex gap-1">
          <Button size="icon" variant="ghost" aria-label="Edit goal" onClick={onEdit}><Pencil className="size-3.5" /></Button>
          <Button size="icon" variant="ghost" aria-label="Delete goal" onClick={onDelete}><Trash2 className="size-3.5" /></Button>
        </div>
      </div>
      <div className="mt-3 flex items-baseline justify-between">
        <span className="num text-lg font-semibold">{money(g.current_amount, { compact: true })}</span>
        <span className="num text-xs text-muted">of {money(g.target_amount, { compact: true })}</span>
      </div>
      <div className="mt-1.5"><Progress value={p.progress_percent} tone={kind === 'SAVINGS' ? 'bg-pos' : 'bg-accent'} /></div>
      <div className="num mt-1 text-right text-xs text-muted">{pct(p.progress_percent, 1)}</div>
      <dl className="mt-3 space-y-1 text-xs">
        <div className="flex justify-between"><dt className="text-muted">Monthly contribution</dt><dd className="num">{money(g.monthly_contribution)}</dd></div>
        <div className="flex justify-between">
          <dt className="text-muted">{kind === 'SAVINGS' ? 'Estimated completion' : 'Projected completion'}</dt>
          <dd className="num">{p.months_to_goal === 0 ? 'Reached' : p.estimated_completion_date ? `${dateFmt(p.estimated_completion_date)} (${p.months_to_goal} mo)` : 'Not reachable at this rate'}</dd>
        </div>
        {g.target_date && (
          <>
            <div className="flex justify-between"><dt className="text-muted">Target date</dt><dd className="num">{dateFmt(g.target_date)}</dd></div>
            <div className="flex justify-between"><dt className="text-muted">Needed per month</dt><dd className="num">{money(p.required_monthly_contribution)}</dd></div>
          </>
        )}
      </dl>
      {p.on_track !== null && (
        <div className={`mt-3 flex items-center gap-1.5 text-xs ${p.on_track ? 'text-pos' : 'text-warn'}`}>
          {p.on_track ? <CalendarCheck className="size-3.5" /> : <AlertTriangle className="size-3.5" />}
          {p.on_track ? 'On track for the target date' : 'Behind the target date at the current contribution'}
        </div>
      )}
      <p className="mt-3 border-t border-line pt-2 text-[11px] leading-snug text-faint">{p.assumption}</p>
    </div>
  )
}
