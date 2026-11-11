import { useState } from 'react'
import { Banknote, CreditCard, LineChart, Pencil, Plus, Trash2 } from 'lucide-react'
import { useApi } from '../lib/hooks'
import { del, patch, post } from '../lib/api'
import { dateFmt, money, pct, titleCase, todayIso } from '../lib/format'
import { Button, Card, EmptyState, ErrorNote, Loading, PageHeader, SourceBadge, Stat, Table, enumOptions } from '../components/ui'
import { ConfirmDialog, FormModal } from '../components/FormModal'

const ACCOUNT_TYPES = ['SAVINGS', 'SALARY', 'CURRENT', 'OTHER']
const LIABILITY_TYPES = ['HOME_LOAN', 'PERSONAL_LOAN', 'CAR_LOAN', 'EDUCATION_LOAN', 'CREDIT_CARD', 'OTHER']

const accountFields = [
  { name: 'bank_name', label: 'Bank', required: true, half: true },
  { name: 'account_label', label: 'Label', placeholder: 'e.g. Salary account', required: true, half: true },
  { name: 'account_type', label: 'Type', type: 'select', required: true, half: true, options: enumOptions(ACCOUNT_TYPES), default: 'SAVINGS' },
  { name: 'last4', label: 'Last 4 digits (optional)', half: true, nullable: true, help: 'Never enter the full account number.' },
  { name: 'balance', label: 'Current balance (₹)', type: 'number', step: '0.01', min: '0', required: true, half: true },
  { name: 'balance_as_of', label: 'Balance as of', type: 'date', half: true, nullable: true, default: todayIso() },
]
const liabilityFields = [
  { name: 'name', label: 'Name', required: true, half: true },
  { name: 'liability_type', label: 'Type', type: 'select', required: true, half: true, options: enumOptions(LIABILITY_TYPES), default: 'PERSONAL_LOAN' },
  { name: 'lender', label: 'Lender (optional)', half: true, nullable: true },
  { name: 'outstanding_amount', label: 'Outstanding (₹)', type: 'number', step: '0.01', min: '0', required: true, half: true },
  { name: 'interest_rate', label: 'Interest rate % (optional)', type: 'number', step: '0.01', min: '0', max: '30', half: true, nullable: true },
  { name: 'emi_amount', label: 'EMI (₹, optional)', type: 'number', step: '0.01', min: '0', half: true, nullable: true },
]

export default function Portfolio() {
  const accounts = useApi('/bank-accounts')
  const liabilities = useApi('/liabilities')
  const dash = useApi('/dashboard')
  const [editing, setEditing] = useState(null)
  const [deleting, setDeleting] = useState(null)
  const path = (k) => (k === 'ACCOUNT' ? '/bank-accounts' : '/liabilities')
  const reload = (k) => {
    ;(k === 'ACCOUNT' ? accounts : liabilities).reload()
    dash.reload()
  }

  async function save(values) {
    if (editing.record) await patch(`${path(editing.kind)}/${editing.record.id}`, values)
    else await post(path(editing.kind), values)
    reload(editing.kind)
  }
  const nw = dash.data?.net_worth
  const rowActions = (kind) => (r) => (
    <div className="flex justify-end gap-1">
      <Button size="icon" variant="ghost" aria-label="Edit" onClick={() => setEditing({ kind, record: r })}><Pencil className="size-3.5" /></Button>
      <Button size="icon" variant="ghost" aria-label="Delete" onClick={() => setDeleting({ kind, record: r })}><Trash2 className="size-3.5" /></Button>
    </div>
  )

  return (
    <div className="fade-in">
      <PageHeader
        title="Portfolio"
        description="Bank balances and liabilities feed your net worth. Market holdings will be added with the Mutual Funds and Stocks modules."
        actions={
          <>
            <Button icon={CreditCard} onClick={() => setEditing({ kind: 'LIABILITY', record: null })}>Add liability</Button>
            <Button variant="primary" icon={Banknote} onClick={() => setEditing({ kind: 'ACCOUNT', record: null })}>Add bank account</Button>
          </>
        }
      />
      {nw && (
        <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
          <Stat label="Bank balances" value={money(nw.bank_balances, { compact: true })} />
          <Stat label="Deposits (FD + RD)" value={money(Number(nw.fixed_deposits) + Number(nw.recurring_deposits), { compact: true })} hint="Current value" />
          <Stat label="Liabilities" value={money(nw.total_liabilities, { compact: true })} tone={Number(nw.total_liabilities) ? 'text-neg' : undefined} />
          <Stat label="Net worth" value={money(nw.net_worth, { compact: true })} tone={Number(nw.net_worth) < 0 ? 'text-neg' : 'text-fg'} />
        </div>
      )}

      <Card className="mt-5" title="Bank accounts">
        <ErrorNote error={accounts.error} />
        {accounts.loading && !accounts.data ? <Loading /> : (
          <Table rows={accounts.data} testId="accounts-table"
            empty={<EmptyState icon={Banknote} title="No bank accounts">Add the balance of each account manually. MaddyView does not connect to banks.</EmptyState>}
            columns={[
              { key: 'bank_name', label: 'Bank', render: (r) => <div className="flex items-center gap-2">{r.bank_name}{r.source !== 'USER_ENTERED' && <SourceBadge source={r.source} />}</div> },
              { key: 'account_label', label: 'Account', render: (r) => <span>{r.account_label}{r.last4 && <span className="text-faint"> ••{r.last4}</span>}</span> },
              { key: 'account_type', label: 'Type', render: (r) => <span className="text-muted">{titleCase(r.account_type)}</span> },
              { key: 'balance_as_of', label: 'As of', render: (r) => <span className="text-muted">{dateFmt(r.balance_as_of)}</span> },
              { key: 'balance', label: 'Balance', align: 'right', render: (r) => money(r.balance) },
              { key: 'a', label: '', align: 'right', render: rowActions('ACCOUNT') },
            ]} />
        )}
      </Card>

      <Card className="mt-5" title="Liabilities">
        <ErrorNote error={liabilities.error} />
        {liabilities.loading && !liabilities.data ? <Loading /> : (
          <Table rows={liabilities.data} testId="liabilities-table"
            empty={<EmptyState icon={CreditCard} title="No liabilities">Loans and card balances you add here reduce your net worth.</EmptyState>}
            columns={[
              { key: 'name', label: 'Name', render: (r) => <div className="flex items-center gap-2">{r.name}{r.source !== 'USER_ENTERED' && <SourceBadge source={r.source} />}</div> },
              { key: 'liability_type', label: 'Type', render: (r) => <span className="text-muted">{titleCase(r.liability_type)}</span> },
              { key: 'lender', label: 'Lender', render: (r) => <span className="text-muted">{r.lender || '—'}</span> },
              { key: 'interest_rate', label: 'Rate', render: (r) => (r.interest_rate ? pct(r.interest_rate) : '—') },
              { key: 'emi_amount', label: 'EMI', align: 'right', render: (r) => money(r.emi_amount) },
              { key: 'outstanding_amount', label: 'Outstanding', align: 'right', render: (r) => <span className="text-neg">{money(r.outstanding_amount)}</span> },
              { key: 'a', label: '', align: 'right', render: rowActions('LIABILITY') },
            ]} />
        )}
      </Card>

      <Card className="mt-5" title="Market holdings">
        <EmptyState icon={LineChart} title="Not available yet">
          Holdings, cost basis and live valuation arrive with the Mutual Funds and Stocks milestones, once a verified price source is connected.
        </EmptyState>
      </Card>

      <FormModal
        open={!!editing}
        title={`${editing?.record ? 'Edit' : 'Add'} ${editing?.kind === 'ACCOUNT' ? 'bank account' : 'liability'}`}
        fields={editing?.kind === 'ACCOUNT' ? accountFields : liabilityFields}
        initial={editing?.record}
        onClose={() => setEditing(null)}
        onSubmit={save}
      />
      <ConfirmDialog
        open={!!deleting}
        title="Delete?"
        message={deleting && `“${deleting.record.name || deleting.record.account_label}” will be permanently removed.`}
        onCancel={() => setDeleting(null)}
        onConfirm={async () => {
          await del(`${path(deleting.kind)}/${deleting.record.id}`)
          reload(deleting.kind)
          setDeleting(null)
        }}
      />
    </div>
  )
}
