import { CandlestickChart, CircleDashed, FlaskConical, LineChart, Newspaper, PieChart, ShieldAlert } from 'lucide-react'
import { Badge, Card, PageHeader } from '../components/ui'

// Honest placeholders for modules scheduled after Milestone 1. They show no numbers at all,
// because no verified data source is connected yet.
function Planned({ title, icon: Icon, milestone, summary, capabilities, dataNeeds, warning }) {
  return (
    <div className="fade-in max-w-4xl">
      <PageHeader title={title} description={summary} actions={<Badge tone="accent">Planned · {milestone}</Badge>} />
      <div className="grid gap-5 md:grid-cols-2">
        <Card title="What this module will do">
          <ul className="space-y-2 text-sm text-muted">
            {capabilities.map((c) => (
              <li key={c} className="flex gap-2"><CircleDashed className="mt-0.5 size-4 shrink-0 text-faint" />{c}</li>
            ))}
          </ul>
        </Card>
        <Card title="Why nothing is shown yet">
          <div className="flex gap-3">
            <Icon className="size-5 shrink-0 text-faint" />
            <div className="space-y-2 text-sm text-muted">
              <p>No verified data source is connected, so MaddyView shows no prices, NAVs or signals rather than sample numbers that could be mistaken for real ones.</p>
              <p className="text-xs text-faint">Needs: {dataNeeds}</p>
            </div>
          </div>
        </Card>
      </div>
      {warning && (
        <p className="mt-5 flex items-start gap-2 rounded-lg border border-warn/30 bg-warn/10 px-3 py-2 text-xs text-warn">
          <ShieldAlert className="mt-0.5 size-4 shrink-0" />{warning}
        </p>
      )}
    </div>
  )
}

export const MutualFunds = () => (
  <Planned title="Mutual Funds" icon={PieChart} milestone="Milestone 2"
    summary="Track mutual-fund holdings and research schemes."
    capabilities={['Record SIPs, lumpsum purchases and redemptions', 'Daily NAV valuation, XIRR and absolute returns', 'Scheme comparison: expense ratio, category, rolling returns', 'Overlap and concentration analysis']}
    dataNeeds="an official NAV source (e.g. AMFI daily NAV file) with ingestion logging." />
)
export const Stocks = () => (
  <Planned title="Stocks" icon={LineChart} milestone="Milestone 2"
    summary="Equity holdings and company research."
    capabilities={['Holdings with cost basis and realised / unrealised P&L', 'Price charts (TradingView Lightweight Charts)', 'Company fundamentals from published filings', 'Watchlists and price alerts']}
    dataNeeds="a licensed end-of-day or delayed price feed with API credentials." />
)
export const MarketIntelligence = () => (
  <Planned title="Market Intelligence" icon={Newspaper} milestone="Milestone 3"
    summary="News and research relevant to what you hold."
    capabilities={['Aggregate news from attributed publishers', 'Link articles to your holdings', 'AI summaries clearly labelled AI_DERIVED']}
    dataNeeds="a news API with terms that allow storage and attribution." />
)
export const Trading = () => (
  <Planned title="Trading Intelligence" icon={CandlestickChart} milestone="Milestone 4"
    summary="Model-based signals for research only."
    capabilities={['Technical indicators on historical data', 'Model predictions with stored confidence and later evaluation', 'Back-testing with transparent assumptions']}
    dataNeeds="historical price data and a registered, evaluated model."
    warning="MaddyView will never place real orders. Predictions are research aids, not financial advice." />
)
export const PaperTrading = () => (
  <Planned title="Paper Trading" icon={FlaskConical} milestone="Milestone 4"
    summary="Practise strategies with simulated money."
    capabilities={['Virtual accounts with simulated cash', 'Market and limit orders against delayed prices', 'Positions, trade history and performance — all labelled SIMULATED']}
    dataNeeds="a price source to fill simulated orders against."
    warning="Simulation only. No brokerage connection exists or will be added for real-money trading." />
)
