import { Link } from 'react-router-dom'
import {
  ArrowDownRight,
  ArrowUpRight,
  Banknote,
  Bot,
  CalendarClock,
  Landmark,
  PiggyBank,
  Receipt,
  Scale,
  Sparkles,
  Target,
  TrendingUp,
  Wallet,
} from 'lucide-react'
import { useState } from 'react'
import { useApi } from '../lib/hooks'
import { post } from '../lib/api'
import { useApp } from '../context/AppContext'
import { dateFmt, money, monthLabel, pct, signClass, titleCase } from '../lib/format'
import { Badge, Button, Card, EmptyState, ErrorNote, Loading, PageHeader, Progress, SourceBadge, Stat, cx } from '../components/ui'

const ALLOC_COLORS = ['#5b8def', '#34d399', '#fbbf24', '#c084fc', '#f472b6', '#22d3ee', '#a3e635', '#fb923c']

export default function Dashboard() {
  const { data: d, error, loading, reload } = useApi('/dashboard')
  const { bumpData, reloadSettings } = useApp()
  const [loadingDemo, setLoadingDemo] = useState(false)

  if (loading && !d) return <Loading />
  if (error) return <ErrorNote error={error} onRetry={reload} />
  const nw = d.net_worth
  const c = d.counts
  const isEmpty = !c.bank_accounts && !c.liabilities && !c.fixed_deposits && !c.recurring_deposits && !c.goals && !c.transactions

  async function loadDemo() {
    setLoadingDemo(true)
    try {
      await post('/demo')
      await reloadSettings()
      bumpData()
    } finally {
      setLoadingDemo(false)
    }
  }

  return (
    <div className="fade-in">
      <PageHeader
        title="Dashboard"
        description={`Your financial position as of ${dateFmt(d.as_of)}. Every figure comes from records you entered${d.includes_demo ? ' plus labelled DEMO records' : ''}.`}
        actions={d.includes_demo && <Badge tone="warn">Includes DEMO data</Badge>}
      />

      {isEmpty && (
        <Card className="mb-5" bodyClass="p-0">
          <EmptyState
            icon={Sparkles}
            title="Your dashboard is empty — nothing has been invented to fill it."
            action={
              <div className="flex flex-wrap justify-center gap-2">
                <Link to="/personal-finance"><Button variant="primary" icon={Receipt}>Record income or expense</Button></Link>
                <Link to="/portfolio"><Button icon={Banknote}>Add bank account</Button></Link>
                <Link to="/deposits"><Button icon={Landmark}>Add FD / RD</Button></Link>
                <Button variant="ghost" onClick={loadDemo} loading={loadingDemo}>Load labelled DEMO data</Button>
              </div>
            }
          >
            Add a bank balance, a deposit or this month's income and expenses. Net worth, savings rate and allocation are calculated from what you enter.
          </EmptyState>
        </Card>
      )}

      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4" data-testid="kpis">
        <Stat label="Net worth" value={money(nw.net_worth, { compact: true })} tone={signClass(nw.net_worth)} icon={Scale}
          hint="Assets − liabilities" testId="kpi-net-worth" />
        <Stat label="Total assets" value={money(nw.total_assets, { compact: true })} icon={Wallet} hint="Bank + deposits + investments" />
        <Stat label="Liabilities" value={money(nw.total_liabilities, { compact: true })} tone={Number(nw.total_liabilities) > 0 ? 'text-neg' : undefined}
          icon={ArrowDownRight} hint={c.liabilities ? `${c.liabilities} tracked` : 'None recorded'} />
        <Stat label="Investments" value={money(d.investments.total_at_cost, { compact: true })} icon={TrendingUp}
          badge={<Badge title={d.investments.valuation_note}>At cost</Badge>} hint="No live prices" />
        <Stat label="Income" value={money(d.month.income, { compact: true })} tone={Number(d.month.income) > 0 ? 'text-pos' : undefined}
          icon={ArrowUpRight} hint={monthLabel(d.month.month)} testId="kpi-income" />
        <Stat label="Expenses" value={money(d.month.expenses, { compact: true })} icon={Receipt} hint={monthLabel(d.month.month)} testId="kpi-expenses" />
        <Stat label="Savings rate" value={d.month.savings_rate === null ? '—' : pct(d.month.savings_rate, 1)}
          tone={d.month.savings_rate === null ? 'text-muted' : signClass(d.month.savings_rate)} icon={PiggyBank}
          hint={d.month.savings_rate === null ? 'No income recorded this month' : `${money(d.month.savings)} saved`} testId="kpi-savings-rate" />
        <Stat label="Goal progress" value={d.goals.overall_progress_percent === null ? '—' : pct(d.goals.overall_progress_percent, 1)}
          icon={Target} hint={d.goals.count ? `${d.goals.count} active goal${d.goals.count > 1 ? 's' : ''}` : 'No goals yet'} />
      </div>

      <div className="mt-5 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        <Card title="Asset allocation" subtitle="Share of total assets">
          {d.allocation.length ? <Allocation items={d.allocation} /> : (
            <EmptyState icon={Wallet} title="No assets recorded">Add bank balances or deposits to see how your assets are spread.</EmptyState>
          )}
        </Card>

        <Card title="Recent transactions" className="xl:col-span-2"
          actions={<Link to="/personal-finance" className="text-xs text-accent hover:underline">View all</Link>}>
          {d.recent_transactions.length ? (
            <ul className="-my-2 divide-y divide-line/60">
              {d.recent_transactions.map((t) => (
                <li key={`${t.kind}-${t.id}`} className="flex items-center gap-3 py-2.5">
                  <div className={cx('grid size-8 shrink-0 place-items-center rounded-lg border border-line', t.kind === 'INCOME' ? 'text-pos' : 'text-neg')}>
                    {t.kind === 'INCOME' ? <ArrowUpRight className="size-4" /> : <ArrowDownRight className="size-4" />}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 text-sm">
                      <span className="truncate">{t.category}</span>
                      {t.source !== 'USER_ENTERED' && <SourceBadge source={t.source} />}
                    </div>
                    <div className="truncate text-xs text-muted">{t.label} · {dateFmt(t.record_date)}</div>
                  </div>
                  <div className={cx('num text-sm font-medium', t.kind === 'INCOME' ? 'text-pos' : 'text-fg')}>
                    {t.kind === 'INCOME' ? '+' : '−'}{money(t.amount)}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState icon={Receipt} title="No transactions yet" action={<Link to="/personal-finance"><Button size="sm">Add a transaction</Button></Link>}>
              Record income and expenses manually in Personal Finance.
            </EmptyState>
          )}
        </Card>

        <Card title="Financial goals" actions={<Link to="/goals" className="text-xs text-accent hover:underline">Manage</Link>}>
          {d.goals.items.length ? (
            <ul className="space-y-4">
              {d.goals.items.map((g) => (
                <li key={`${g.kind}-${g.id}`}>
                  <div className="mb-1 flex items-center justify-between gap-2 text-sm">
                    <span className="flex min-w-0 items-center gap-2">
                      <span className="truncate">{g.name}</span>
                      {g.source === 'DEMO' && <SourceBadge source="DEMO" />}
                    </span>
                    <span className="num text-xs text-muted">{pct(g.progress_percent, 0)}</span>
                  </div>
                  <Progress value={g.progress_percent} tone={g.kind === 'SAVINGS' ? 'bg-pos' : 'bg-accent'} />
                  <div className="num mt-1 text-xs text-faint">{money(g.current_amount, { compact: true })} of {money(g.target_amount, { compact: true })}</div>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState icon={Target} title="No goals yet">Set a savings or investment goal to track progress here.</EmptyState>
          )}
        </Card>

        <Card title="Upcoming FD / RD maturities" subtitle="Next 90 days" actions={<Link to="/deposits" className="text-xs text-accent hover:underline">Deposits</Link>}>
          {d.upcoming_maturities.length ? (
            <ul className="-my-2 divide-y divide-line/60">
              {d.upcoming_maturities.map((m) => (
                <li key={`${m.kind}-${m.id}`} className="flex items-center justify-between gap-3 py-2.5">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 text-sm">
                      <Badge tone="accent">{m.kind}</Badge>
                      <span className="truncate">{m.bank_name}</span>
                      {m.source === 'DEMO' && <SourceBadge source="DEMO" />}
                    </div>
                    <div className="mt-0.5 text-xs text-muted">{dateFmt(m.maturity_date)} · in {m.days_to_maturity} days</div>
                  </div>
                  <div className="text-right">
                    <div className="num text-sm">{money(m.gross_maturity_value)}</div>
                    <div className="text-[10px] uppercase tracking-wide text-faint">Gross</div>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState icon={CalendarClock} title="Nothing maturing soon">Deposits maturing in the next 90 days appear here.</EmptyState>
          )}
        </Card>

        <Card title="AI research reports">
          <EmptyState icon={Bot} title="No reports generated">
            {d.ai_reports_note} MaddyView will not show sample reports as if they were real research.
          </EmptyState>
        </Card>
      </div>
    </div>
  )
}

function Allocation({ items }) {
  return (
    <div>
      <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-surface-2" aria-hidden>
        {items.map((a, i) => (
          <div key={a.asset_class} style={{ width: `${a.percent}%`, background: ALLOC_COLORS[i % ALLOC_COLORS.length] }} />
        ))}
      </div>
      <ul className="mt-4 space-y-2.5">
        {items.map((a, i) => (
          <li key={a.asset_class} className="flex items-start gap-2 text-sm">
            <span className="mt-1.5 size-2.5 shrink-0 rounded-sm" style={{ background: ALLOC_COLORS[i % ALLOC_COLORS.length] }} />
            <div className="min-w-0 flex-1">
              <div className="flex items-baseline justify-between gap-2">
                <span className="truncate">{a.asset_class}</span>
                <span className="num shrink-0">{money(a.amount, { compact: true })}</span>
              </div>
              <div className="num text-xs text-muted">{pct(a.percent, 1)} of assets</div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
