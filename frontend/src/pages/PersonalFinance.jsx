import { useMemo, useState } from 'react'
import { ArrowDownRight, ArrowUpRight, Pencil, PiggyBank, Plus, Receipt, Trash2 } from 'lucide-react'
import { useApi } from '../lib/hooks'
import { del, get, patch, post } from '../lib/api'
import { currentMonth, dateFmt, money, monthLabel, pct, signClass, titleCase, todayIso } from '../lib/format'
import { Button, Card, EmptyState, ErrorNote, Loading, PageHeader, Segmented, SourceBadge, Stat, Table, cx, enumOptions } from '../components/ui'
import { ConfirmDialog, FormModal } from '../components/FormModal'

const PAYMENT_METHODS = ['UPI', 'DEBIT_CARD', 'CREDIT_CARD', 'NET_BANKING', 'CASH', 'CHEQUE', 'OTHER']
const INCOME_CATS = ['Salary', 'Freelance', 'Business', 'Interest', 'Dividend', 'Rental', 'Gift', 'Refund', 'Other']
const EXPENSE_CATS = ['Rent', 'Groceries', 'Utilities', 'Dining', 'Transport', 'Fuel', 'Shopping', 'Health', 'Insurance', 'Education', 'EMI', 'Entertainment', 'Travel', 'Other']

const selectCls = 'h-9 rounded-lg border border-line bg-surface-2 px-2.5 text-sm text-fg focus:border-accent focus:outline-none'

export default function PersonalFinance() {
  const [month, setMonth] = useState(currentMonth())
  const [tab, setTab] = useState('ALL')
  const [category, setCategory] = useState('')
  const [editing, setEditing] = useState(null) // { kind, record|null }
  const [deleting, setDeleting] = useState(null)

  const q = new URLSearchParams()
  if (month) q.set('month', month)
  if (category) q.set('category', category)
  if (tab !== 'ALL') q.set('kind', tab)
  const tx = useApi(`/finance/transactions?${q}`)
  const summary = useApi(`/finance/summary?month=${month || currentMonth()}`)
  const trend = useApi('/finance/trend?months=6')
  const accounts = useApi('/bank-accounts')
  const incomeCats = useApi('/income-categories')
  const expenseCats = useApi('/expense-categories')

  const reloadAll = () => [tx, summary, trend, incomeCats, expenseCats].forEach((r) => r.reload())
  const allCats = useMemo(
    () => [...new Set([...(incomeCats.data || []), ...(expenseCats.data || [])])].sort(),
    [incomeCats.data, expenseCats.data],
  )
  const accountOptions = (accounts.data || []).map((a) => ({ value: String(a.id), label: `${a.bank_name} · ${a.account_label}` }))

  const incomeFields = [
    { name: 'amount', label: 'Amount (₹)', type: 'number', step: '0.01', min: '0.01', required: true, half: true },
    { name: 'record_date', label: 'Date', type: 'date', required: true, half: true, default: todayIso() },
    { name: 'income_source', label: 'Source', placeholder: 'Employer, client…', required: true, half: true },
    { name: 'category', label: 'Category', required: true, half: true, list: [...new Set([...INCOME_CATS, ...(incomeCats.data || [])])] },
    ...(accountOptions.length ? [{ name: 'bank_account_id', label: 'Credited to account', type: 'select', options: accountOptions, nullable: true }] : []),
    { name: 'description', label: 'Description', type: 'textarea', nullable: true },
  ]
  const expenseFields = [
    { name: 'amount', label: 'Amount (₹)', type: 'number', step: '0.01', min: '0.01', required: true, half: true },
    { name: 'record_date', label: 'Date', type: 'date', required: true, half: true, default: todayIso() },
    { name: 'category', label: 'Category', required: true, half: true, list: [...new Set([...EXPENSE_CATS, ...(expenseCats.data || [])])] },
    { name: 'payment_method', label: 'Payment method', type: 'select', required: true, half: true, options: enumOptions(PAYMENT_METHODS), default: 'UPI' },
    ...(accountOptions.length ? [{ name: 'bank_account_id', label: 'Paid from account', type: 'select', options: accountOptions, nullable: true }] : []),
    { name: 'description', label: 'Description', type: 'textarea', nullable: true },
  ]

  async function save(values) {
    const kind = editing.kind
    const base = kind === 'INCOME' ? '/income' : '/expenses'
    if (values.bank_account_id) values.bank_account_id = Number(values.bank_account_id)
    if (editing.record) await patch(`${base}/${editing.record.id}`, values)
    else await post(base, values)
    reloadAll()
  }

  async function openEdit(row) {
    const base = row.kind === 'INCOME' ? '/income' : '/expenses'
    const rec = await get(`${base}/${row.id}`)
    setEditing({ kind: row.kind, record: { ...rec, bank_account_id: rec.bank_account_id ? String(rec.bank_account_id) : '' } })
  }

  const s = summary.data
  return (
    <div className="fade-in">
      <PageHeader
        title="Personal Finance"
        description="Record income and expenses manually. Savings = income − expenses; savings rate = savings ÷ income."
        actions={
          <>
            <Button icon={ArrowUpRight} onClick={() => setEditing({ kind: 'INCOME', record: null })}>Add income</Button>
            <Button variant="primary" icon={ArrowDownRight} onClick={() => setEditing({ kind: 'EXPENSE', record: null })}>Add expense</Button>
          </>
        }
      />

      <div className="mb-4 flex flex-wrap items-center gap-2">
        <input type="month" aria-label="Filter by month" value={month} onChange={(e) => setMonth(e.target.value)} className={cx(selectCls, 'w-44')} />
        <Button size="sm" variant="ghost" onClick={() => setMonth(month ? '' : currentMonth())}>{month ? 'All months' : 'This month'}</Button>
        <select aria-label="Filter by category" value={category} onChange={(e) => setCategory(e.target.value)} className={cx(selectCls, 'w-44')}>
          <option value="">All categories</option>
          {allCats.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {s && (
        <div className="grid grid-cols-2 gap-3 xl:grid-cols-4" data-testid="pf-summary">
          <Stat label={`Income · ${monthLabel(s.month)}`} value={money(s.total_income)} tone={Number(s.total_income) ? 'text-pos' : undefined} hint={`${s.income_count} record(s)`} />
          <Stat label="Expenses" value={money(s.total_expenses)} hint={`${s.expense_count} record(s)`} />
          <Stat label="Savings" value={money(s.savings)} tone={signClass(s.savings)} hint="Income − expenses" icon={PiggyBank} testId="pf-savings" />
          <Stat label="Savings rate" value={s.savings_rate === null ? '—' : pct(s.savings_rate, 1)} tone={s.savings_rate === null ? 'text-muted' : signClass(s.savings_rate)}
            hint={s.savings_rate_note || 'Savings ÷ income'} testId="pf-savings-rate" />
        </div>
      )}

      <div className="mt-5 grid gap-5 lg:grid-cols-3">
        <Card
          className="lg:col-span-2"
          title="Transaction history"
          subtitle={month ? monthLabel(month) : 'All months'}
          actions={<Segmented value={tab} onChange={setTab} options={[{ value: 'ALL', label: 'All' }, { value: 'INCOME', label: 'Income' }, { value: 'EXPENSE', label: 'Expenses' }]} />}
        >
          <ErrorNote error={tx.error} onRetry={tx.reload} />
          {tx.loading && !tx.data ? <Loading /> : (
            <Table
              testId="tx-table"
              rows={tx.data}
              rowKey={(r) => `${r.kind}-${r.id}`}
              empty={
                <EmptyState icon={Receipt} title={category ? 'No transactions match these filters' : month ? `No transactions in ${monthLabel(month)}` : 'No transactions yet'}>
                  Use “Add income” or “Add expense” to record one. Nothing is imported automatically.
                </EmptyState>
              }
              columns={[
                { key: 'record_date', label: 'Date', render: (r) => <span className="whitespace-nowrap text-muted">{dateFmt(r.record_date)}</span> },
                { key: 'category', label: 'Category', render: (r) => (
                  <div className="flex items-center gap-2">
                    <span className={cx('size-1.5 rounded-full', r.kind === 'INCOME' ? 'bg-pos' : 'bg-neg')} />
                    <span>{r.category}</span>
                    {r.source !== 'USER_ENTERED' && <SourceBadge source={r.source} />}
                  </div>
                ) },
                { key: 'label', label: 'Source / method', render: (r) => <span className="text-muted">{r.label}</span> },
                { key: 'description', label: 'Note', render: (r) => <span className="line-clamp-1 max-w-48 text-muted">{r.description || ''}</span> },
                { key: 'amount', label: 'Amount', align: 'right', render: (r) => (
                  <span className={r.kind === 'INCOME' ? 'text-pos' : ''}>{r.kind === 'INCOME' ? '+' : '−'}{money(r.amount)}</span>
                ) },
                { key: 'actions', label: '', align: 'right', render: (r) => (
                  <div className="flex justify-end gap-1">
                    <Button size="icon" variant="ghost" aria-label="Edit" onClick={() => openEdit(r)}><Pencil className="size-3.5" /></Button>
                    <Button size="icon" variant="ghost" aria-label="Delete" onClick={() => setDeleting(r)}><Trash2 className="size-3.5" /></Button>
                  </div>
                ) },
              ]}
            />
          )}
        </Card>

        <div className="flex flex-col gap-5">
          <Card title="Expense breakdown" subtitle={s ? monthLabel(s.month) : ''}>
            {s?.expense_breakdown.length ? (
              <ul className="space-y-3">
                {s.expense_breakdown.map((b) => (
                  <li key={b.category}>
                    <div className="mb-1 flex justify-between text-sm">
                      <span className="truncate">{b.category}</span>
                      <span className="num text-muted">{money(b.amount)} · {pct(b.percent, 0)}</span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-surface-2">
                      <div className="h-full rounded-full bg-neg/70" style={{ width: `${b.percent}%` }} />
                    </div>
                  </li>
                ))}
              </ul>
            ) : <EmptyState title="No expenses this month" />}
          </Card>
          <Card title="Last 6 months" subtitle="Income vs expenses">
            {trend.data ? <Trend points={trend.data} /> : <Loading />}
          </Card>
        </div>
      </div>

      <FormModal
        open={!!editing}
        title={`${editing?.record ? 'Edit' : 'Add'} ${editing?.kind === 'INCOME' ? 'income' : 'expense'}`}
        fields={editing?.kind === 'INCOME' ? incomeFields : expenseFields}
        initial={editing?.record}
        onClose={() => setEditing(null)}
        onSubmit={save}
      />
      <ConfirmDialog
        open={!!deleting}
        title={`Delete ${deleting?.kind === 'INCOME' ? 'income' : 'expense'}?`}
        message={deleting && `${titleCase(deleting.category)} · ${money(deleting.amount)} on ${dateFmt(deleting.record_date)} will be permanently removed.`}
        onCancel={() => setDeleting(null)}
        onConfirm={async () => {
          await del(`${deleting.kind === 'INCOME' ? '/income' : '/expenses'}/${deleting.id}`)
          setDeleting(null)
          reloadAll()
        }}
      />
    </div>
  )
}

function Trend({ points }) {
  const max = Math.max(1, ...points.flatMap((p) => [Number(p.income), Number(p.expenses)]))
  const hasData = points.some((p) => Number(p.income) || Number(p.expenses))
  if (!hasData) return <EmptyState title="No history yet">Bars appear once you record transactions.</EmptyState>
  return (
    <div>
      <div className="flex h-32 items-end gap-2">
        {points.map((p) => (
          <div key={p.month} className="flex flex-1 items-end justify-center gap-0.5" title={`${monthLabel(p.month)}: income ${money(p.income)}, expenses ${money(p.expenses)}`}>
            <div className="w-2.5 rounded-t bg-pos/80" style={{ height: `${(Number(p.income) / max) * 100}%` }} />
            <div className="w-2.5 rounded-t bg-neg/70" style={{ height: `${(Number(p.expenses) / max) * 100}%` }} />
          </div>
        ))}
      </div>
      <div className="mt-1.5 flex gap-2">
        {points.map((p) => (
          <div key={p.month} className="flex-1 text-center text-[10px] text-faint">
            {new Date(p.month + '-01').toLocaleDateString('en-IN', { month: 'short' })}
          </div>
        ))}
      </div>
      <div className="mt-3 flex gap-4 text-xs text-muted">
        <span className="flex items-center gap-1.5"><span className="size-2 rounded-sm bg-pos/80" />Income</span>
        <span className="flex items-center gap-1.5"><span className="size-2 rounded-sm bg-neg/70" />Expenses</span>
      </div>
    </div>
  )
}
