import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import {
  BarChart3,
  Briefcase,
  CandlestickChart,
  FlaskConical,
  Gauge,
  Landmark,
  LineChart,
  LogOut,
  Menu,
  Moon,
  Newspaper,
  PieChart,
  Settings,
  Sun,
  Target,
  Wallet,
  X,
} from 'lucide-react'
import { useApp } from '../context/AppContext'
import { Button, cx } from './ui'

export const NAV = [
  { to: '/', label: 'Dashboard', icon: Gauge, end: true },
  { to: '/personal-finance', label: 'Personal Finance', icon: Wallet },
  { to: '/deposits', label: 'FD & RD', icon: Landmark },
  { to: '/goals', label: 'Financial Goals', icon: Target },
  { to: '/portfolio', label: 'Portfolio', icon: Briefcase },
  { section: 'Research' },
  { to: '/mutual-funds', label: 'Mutual Funds', icon: PieChart, soon: true },
  { to: '/stocks', label: 'Stocks', icon: LineChart, soon: true },
  { to: '/market-intelligence', label: 'Market Intelligence', icon: Newspaper, soon: true },
  { section: 'Trading' },
  { to: '/trading', label: 'Trading', icon: CandlestickChart, soon: true },
  { to: '/paper-trading', label: 'Paper Trading', icon: FlaskConical, soon: true },
  { section: 'System' },
  { to: '/settings', label: 'Settings', icon: Settings },
]

function Brand() {
  return (
    <div className="flex items-center gap-2 px-2">
      <div className="grid size-7 place-items-center rounded-lg border border-line bg-surface-2">
        <BarChart3 className="size-4 text-pos" aria-hidden />
      </div>
      <div className="leading-tight">
        <div className="text-sm font-semibold tracking-tight">MaddyView</div>
        <div className="text-[10px] uppercase tracking-widest text-faint">Personal finance terminal</div>
      </div>
    </div>
  )
}

function NavList({ onNavigate }) {
  return (
    <nav className="mt-6 flex flex-col gap-0.5" aria-label="Main">
      {NAV.map((item, i) =>
        item.section ? (
          <div key={i} className="mt-4 mb-1 px-3 text-[10px] font-semibold uppercase tracking-widest text-faint">
            {item.section}
          </div>
        ) : (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            onClick={onNavigate}
            className={({ isActive }) =>
              cx(
                'group flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition',
                isActive ? 'bg-surface-2 text-fg shadow-[inset_2px_0_0_var(--accent)]' : 'text-muted hover:bg-surface-2/60 hover:text-fg',
              )
            }
          >
            <item.icon className="size-4 shrink-0" aria-hidden />
            <span className="flex-1 truncate">{item.label}</span>
            {item.soon && <span className="rounded border border-line px-1 text-[9px] uppercase tracking-wider text-faint">Soon</span>}
          </NavLink>
        ),
      )}
    </nav>
  )
}

export default function Layout() {
  const { auth, theme, setTheme, logout, settings } = useApp()
  const [open, setOpen] = useState(false)
  const loc = useLocation()
  useEffect(() => setOpen(false), [loc.pathname])

  const sidebarFooter = (
    <div className="mt-auto border-t border-line pt-3">
      <div className="flex items-center justify-between gap-2 px-2">
        <div className="min-w-0">
          <div className="truncate text-sm">{auth.user?.display_name}</div>
          <div className="truncate text-xs text-faint">{auth.user?.email}</div>
        </div>
        <div className="flex gap-1">
          <Button variant="ghost" size="icon" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} aria-label="Toggle theme" title="Toggle theme">
            {theme === 'dark' ? <Sun className="size-4" /> : <Moon className="size-4" />}
          </Button>
          <Button variant="ghost" size="icon" onClick={logout} aria-label="Sign out" title="Sign out">
            <LogOut className="size-4" />
          </Button>
        </div>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[240px_1fr]">
      {/* desktop sidebar */}
      <aside className="sticky top-0 hidden h-screen flex-col overflow-y-auto border-r border-line bg-surface px-3 py-4 lg:flex">
        <Brand />
        <NavList />
        {sidebarFooter}
      </aside>

      {/* mobile top bar + drawer */}
      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-line bg-surface/95 px-4 py-2.5 backdrop-blur lg:hidden">
        <Brand />
        <Button variant="ghost" size="icon" onClick={() => setOpen(true)} aria-label="Open menu">
          <Menu className="size-5" />
        </Button>
      </header>
      {open && (
        <div className="fixed inset-0 z-40 bg-black/60 lg:hidden" onClick={() => setOpen(false)}>
          <aside className="fade-in flex h-full w-72 max-w-[85vw] flex-col overflow-y-auto border-r border-line bg-surface px-3 py-4" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <Brand />
              <Button variant="ghost" size="icon" onClick={() => setOpen(false)} aria-label="Close menu">
                <X className="size-4" />
              </Button>
            </div>
            <NavList onNavigate={() => setOpen(false)} />
            {sidebarFooter}
          </aside>
        </div>
      )}

      <main className="min-w-0">
        {settings?.include_demo_data && (
          <div className="border-b border-demo/30 bg-demo/10 px-4 py-1.5 text-center text-xs text-demo" role="status" data-testid="demo-banner">
            DEMO data is visible. DEMO rows are illustrative, fictional and labelled — turn them off in Settings.
          </div>
        )}
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
