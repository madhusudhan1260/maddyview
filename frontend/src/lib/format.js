// Money arrives from the API as decimal strings ("1234.50"). We convert to Number only
// for display formatting; no arithmetic on money happens in the browser.
const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2, minimumFractionDigits: 2 })
const inrCompact = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', notation: 'compact', maximumFractionDigits: 2 })

export function money(value, { compact = false } = {}) {
  if (value === null || value === undefined || value === '') return '—'
  const n = Number(value)
  if (!Number.isFinite(n)) return '—'
  return (compact && Math.abs(n) >= 100000 ? inrCompact : inr).format(n)
}

export function pct(value, digits = 2) {
  if (value === null || value === undefined) return '—'
  const n = Number(value)
  return Number.isFinite(n) ? `${n.toFixed(digits)}%` : '—'
}

export function signClass(value) {
  const n = Number(value)
  if (!Number.isFinite(n) || n === 0) return 'text-fg'
  return n > 0 ? 'text-pos' : 'text-neg'
}

const dfmt = new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
export function dateFmt(iso) {
  if (!iso) return '—'
  const [y, m, d] = iso.slice(0, 10).split('-').map(Number)
  return dfmt.format(new Date(y, m - 1, d))
}

export function monthLabel(ym) {
  const [y, m] = ym.split('-').map(Number)
  return new Date(y, m - 1, 1).toLocaleDateString('en-IN', { month: 'long', year: 'numeric' })
}

export function currentMonth() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

export function todayIso() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

export const titleCase = (s) => (s || '').replaceAll('_', ' ').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase())
