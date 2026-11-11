import { useEffect, useRef } from 'react'
import { AlertTriangle, Loader2, X } from 'lucide-react'
import { titleCase } from '../lib/format'

export const cx = (...c) => c.filter(Boolean).join(' ')

export function Card({ title, subtitle, actions, children, className, bodyClass, ...rest }) {
  return (
    <section className={cx('rounded-xl border border-line bg-surface min-w-0', className)} {...rest}>
      {(title || actions) && (
        <header className="flex items-start justify-between gap-3 border-b border-line px-4 py-3">
          <div className="min-w-0">
            {title && <h2 className="text-sm font-semibold tracking-tight text-fg">{title}</h2>}
            {subtitle && <p className="mt-0.5 text-xs text-muted">{subtitle}</p>}
          </div>
          {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
        </header>
      )}
      <div className={cx('p-4', bodyClass)}>{children}</div>
    </section>
  )
}

export function Stat({ label, value, hint, tone, badge, icon: Icon, testId }) {
  return (
    <div className="min-w-0 rounded-xl border border-line bg-surface px-4 py-3" data-testid={testId}>
      <div className="flex items-center justify-between gap-2">
        <span className="truncate text-xs font-medium uppercase tracking-wide text-muted">{label}</span>
        {Icon && <Icon className="size-4 shrink-0 text-faint" aria-hidden />}
      </div>
      <div className={cx('num mt-1.5 truncate text-xl font-semibold tracking-tight', tone || 'text-fg')}>{value}</div>
      <div className="mt-1 flex min-h-4 items-center gap-1.5 text-xs text-muted">
        {badge}
        {hint && <span className="truncate">{hint}</span>}
      </div>
    </div>
  )
}

const SOURCE_STYLE = {
  DEMO: 'border-demo/40 bg-demo/10 text-demo',
  USER_ENTERED: 'border-line-strong text-muted',
  REAL: 'border-pos/40 bg-pos/10 text-pos',
  SIMULATED: 'border-accent/40 bg-accent/10 text-accent',
  AI_DERIVED: 'border-warn/40 bg-warn/10 text-warn',
}
const SOURCE_TEXT = { USER_ENTERED: 'Manual', AI_DERIVED: 'AI', DEMO: 'DEMO', REAL: 'Verified', SIMULATED: 'Simulated' }

export function SourceBadge({ source, className }) {
  if (!source) return null
  return (
    <span
      title={`Data source: ${source}`}
      className={cx('inline-flex items-center rounded border px-1.5 py-px text-[10px] font-semibold uppercase tracking-wider', SOURCE_STYLE[source], className)}
    >
      {SOURCE_TEXT[source] || source}
    </span>
  )
}

export function Badge({ tone = 'muted', children, title }) {
  const tones = {
    muted: 'border-line-strong text-muted',
    warn: 'border-warn/40 bg-warn/10 text-warn',
    pos: 'border-pos/40 bg-pos/10 text-pos',
    neg: 'border-neg/40 bg-neg/10 text-neg',
    accent: 'border-accent/40 bg-accent/10 text-accent',
  }
  return (
    <span title={title} className={cx('inline-flex items-center gap-1 rounded border px-1.5 py-px text-[10px] font-semibold uppercase tracking-wider', tones[tone])}>
      {children}
    </span>
  )
}

export function Button({ variant = 'secondary', size = 'md', icon: Icon, children, className, loading, ...rest }) {
  const v = {
    primary: 'bg-accent text-accent-fg hover:brightness-110 border-transparent',
    secondary: 'bg-surface-2 text-fg border-line hover:border-line-strong',
    ghost: 'bg-transparent text-muted border-transparent hover:text-fg hover:bg-surface-2',
    danger: 'bg-neg/10 text-neg border-neg/30 hover:bg-neg/20',
  }[variant]
  const s = { sm: 'h-7 px-2 text-xs gap-1', md: 'h-9 px-3 text-sm gap-1.5', icon: 'size-8 justify-center' }[size]
  return (
    <button
      className={cx('inline-flex shrink-0 items-center rounded-lg border font-medium transition disabled:cursor-not-allowed disabled:opacity-50', v, s, className)}
      disabled={loading || rest.disabled}
      {...rest}
    >
      {loading ? <Loader2 className="size-4 animate-spin" /> : Icon && <Icon className="size-4" aria-hidden />}
      {children}
    </button>
  )
}

export function EmptyState({ icon: Icon, title, children, action }) {
  return (
    <div className="flex flex-col items-center px-4 py-8 text-center">
      {Icon && (
        <div className="mb-3 rounded-full border border-line bg-surface-2 p-2.5">
          <Icon className="size-5 text-muted" aria-hidden />
        </div>
      )}
      <p className="text-sm font-medium text-fg">{title}</p>
      {children && <div className="mt-1 max-w-sm text-xs leading-relaxed text-muted">{children}</div>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

export function Loading({ label = 'Loading…' }) {
  return (
    <div className="flex items-center gap-2 px-1 py-6 text-sm text-muted" role="status">
      <Loader2 className="size-4 animate-spin" /> {label}
    </div>
  )
}

export function ErrorNote({ error, onRetry }) {
  if (!error) return null
  return (
    <div className="flex items-start gap-2 rounded-lg border border-neg/30 bg-neg/10 px-3 py-2 text-sm text-neg" role="alert">
      <AlertTriangle className="mt-0.5 size-4 shrink-0" />
      <div className="min-w-0 flex-1">{error.message || String(error)}</div>
      {onRetry && (
        <button className="text-xs underline" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  )
}

export function PageHeader({ title, description, actions }) {
  return (
    <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        <h1 className="text-xl font-semibold tracking-tight text-fg">{title}</h1>
        {description && <p className="mt-1 max-w-2xl text-sm text-muted">{description}</p>}
      </div>
      {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
    </div>
  )
}

export function Progress({ value, tone = 'bg-accent' }) {
  const v = Math.max(0, Math.min(100, Number(value) || 0))
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-2" role="progressbar" aria-valuenow={v} aria-valuemin={0} aria-valuemax={100}>
      <div className={cx('h-full rounded-full transition-[width] duration-500', tone)} style={{ width: `${v}%` }} />
    </div>
  )
}

export function Modal({ open, title, onClose, children, footer, wide }) {
  const ref = useRef(null)
  useEffect(() => {
    if (!open) return
    const onKey = (e) => e.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    const first = ref.current?.querySelector('input,select,textarea,button')
    first?.focus()
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onClose])
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 sm:items-center sm:p-4" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div
        ref={ref}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={cx('fade-in flex max-h-[92vh] w-full flex-col rounded-t-2xl border border-line bg-surface shadow-2xl sm:rounded-2xl', wide ? 'sm:max-w-3xl' : 'sm:max-w-lg')}
      >
        <div className="flex items-center justify-between border-b border-line px-4 py-3">
          <h2 className="text-sm font-semibold">{title}</h2>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close">
            <X className="size-4" />
          </Button>
        </div>
        <div className="overflow-y-auto px-4 py-4">{children}</div>
        {footer && <div className="flex justify-end gap-2 border-t border-line px-4 py-3">{footer}</div>}
      </div>
    </div>
  )
}

export function Segmented({ value, onChange, options }) {
  return (
    <div className="inline-flex rounded-lg border border-line bg-surface-2 p-0.5" role="tablist">
      {options.map((o) => (
        <button
          key={o.value}
          role="tab"
          aria-selected={value === o.value}
          onClick={() => onChange(o.value)}
          className={cx('rounded-md px-3 py-1 text-xs font-medium transition', value === o.value ? 'bg-surface text-fg shadow-sm' : 'text-muted hover:text-fg')}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}

export function Table({ columns, rows, rowKey = (r) => r.id, empty, onRowClick, testId }) {
  if (!rows?.length) return empty || null
  const dataCols = columns.filter((c) => c.label)
  const actionCols = columns.filter((c) => !c.label)
  return (
    <div data-testid={testId}>
      {/* phones: stacked cards */}
      <ul className="-my-2 divide-y divide-line/60 sm:hidden">
        {rows.map((r) => (
          <li key={rowKey(r)} className={cx('py-3', r.source === 'DEMO' && 'bg-demo/[0.04]')}>
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0 text-sm font-medium">{dataCols[0].render ? dataCols[0].render(r) : r[dataCols[0].key]}</div>
              {actionCols.map((c) => <div key={c.key} className="-mt-1 shrink-0">{c.render(r)}</div>)}
            </div>
            <dl className="mt-1.5 grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
              {dataCols.slice(1).map((c) => (
                <div key={c.key} className="min-w-0">
                  <dt className="text-[10px] uppercase tracking-wide text-faint">{c.label}</dt>
                  <dd className={cx('min-w-0 break-words', c.align === 'right' && 'num')}>{c.render ? c.render(r) : r[c.key]}</dd>
                </div>
              ))}
            </dl>
          </li>
        ))}
      </ul>
      <div className="-mx-4 hidden overflow-x-auto sm:block">
      <table className="w-full min-w-[560px] text-sm">
        <thead>
          <tr className="border-b border-line text-left text-[11px] font-medium uppercase tracking-wide text-muted">
            {columns.map((c) => (
              <th key={c.key} className={cx('px-4 py-2 font-medium', c.align === 'right' && 'text-right')}>
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr
              key={rowKey(r)}
              onClick={onRowClick ? () => onRowClick(r) : undefined}
              className={cx('border-b border-line/60 last:border-0', r.source === 'DEMO' && 'bg-demo/[0.04]', onRowClick && 'cursor-pointer hover:bg-surface-2')}
            >
              {columns.map((c) => (
                <td key={c.key} className={cx('px-4 py-2.5 align-middle', c.align === 'right' && 'num text-right', c.className)}>
                  {c.render ? c.render(r) : r[c.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </div>
  )
}

export const enumOptions = (values) => values.map((v) => ({ value: v, label: titleCase(v) }))
