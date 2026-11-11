import { useEffect, useState } from 'react'
import { Button, Modal, cx } from './ui'
import { ApiError } from '../lib/api'

/**
 * Generic create/edit dialog driven by field definitions.
 * field: { name, label, type: text|number|date|select|textarea|checkbox, options, required, step, min, max,
 *          placeholder, help, list (datalist options), half (two-column on wide screens), nullable }
 * onSubmit(values) must return a promise; ApiError field errors are shown inline.
 */
export function FormModal({ open, title, fields, initial, onClose, onSubmit, submitLabel = 'Save', aside, onChange, wide }) {
  const [values, setValues] = useState({})
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!open) return
    const v = {}
    for (const f of fields) v[f.name] = initial?.[f.name] ?? f.default ?? (f.type === 'checkbox' ? false : '')
    setValues(v)
    setErrors({})
    setFormError(null)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, initial])

  useEffect(() => {
    if (open) onChange?.(values)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [values, open])

  const set = (name, value) => setValues((v) => ({ ...v, [name]: value }))

  async function submit(e) {
    e.preventDefault()
    const missing = {}
    for (const f of fields) if (f.required && (values[f.name] === '' || values[f.name] == null)) missing[f.name] = 'Required'
    if (Object.keys(missing).length) return setErrors(missing)
    const out = {}
    for (const f of fields) {
      let v = values[f.name]
      if (f.type === 'number' && v !== '') v = String(v)
      if (f.type === 'number' && f.integer && v !== '') v = Number(v)
      if (v === '') v = f.nullable || initial ? null : undefined
      if (v !== undefined) out[f.name] = v
    }
    setSaving(true)
    setFormError(null)
    try {
      await onSubmit(out)
      onClose()
    } catch (err) {
      if (err instanceof ApiError) {
        setErrors(err.fieldErrors)
        setFormError(Object.keys(err.fieldErrors).length ? 'Please fix the highlighted fields.' : err.message)
      } else setFormError(String(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open={open}
      title={title}
      onClose={onClose}
      wide={wide || !!aside}
      footer={
        <>
          <Button variant="ghost" onClick={onClose} type="button">
            Cancel
          </Button>
          <Button variant="primary" type="submit" form="fp-form" loading={saving}>
            {submitLabel}
          </Button>
        </>
      }
    >
      <div className={cx(aside && 'grid gap-5 md:grid-cols-[1fr_280px]')}>
        <form id="fp-form" onSubmit={submit} noValidate className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {formError && <p className="col-span-full rounded-lg border border-neg/30 bg-neg/10 px-3 py-2 text-xs text-neg" role="alert">{formError}</p>}
          {fields.map((f) => (
            <Field key={f.name} f={f} value={values[f.name]} error={errors[f.name]} onChange={(v) => set(f.name, v)} />
          ))}
        </form>
        {aside && <aside className="min-w-0">{aside}</aside>}
      </div>
    </Modal>
  )
}

const inputCls =
  'h-9 w-full rounded-lg border bg-surface-2 px-2.5 text-sm text-fg placeholder:text-faint focus:border-accent focus:outline-none focus:ring-2 focus:ring-[var(--ring)]'

function Field({ f, value, error, onChange }) {
  const id = `f-${f.name}`
  const border = error ? 'border-neg' : 'border-line'
  const span = f.half ? '' : 'sm:col-span-2'
  if (f.type === 'checkbox') {
    return (
      <label className={cx('flex items-start gap-2 text-sm', span)} htmlFor={id}>
        <input id={id} type="checkbox" checked={!!value} onChange={(e) => onChange(e.target.checked)} className="mt-0.5 size-4 accent-[var(--accent)]" />
        <span>
          {f.label}
          {f.help && <span className="block text-xs text-muted">{f.help}</span>}
        </span>
      </label>
    )
  }
  let control
  if (f.type === 'select') {
    control = (
      <select id={id} value={value ?? ''} onChange={(e) => onChange(e.target.value)} className={cx(inputCls, border)}>
        {!f.required && <option value="">—</option>}
        {f.options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    )
  } else if (f.type === 'textarea') {
    control = <textarea id={id} rows={2} value={value ?? ''} onChange={(e) => onChange(e.target.value)} placeholder={f.placeholder} className={cx(inputCls, border, 'h-auto py-2')} />
  } else {
    control = (
      <>
        <input
          id={id}
          type={f.type || 'text'}
          inputMode={f.type === 'number' ? 'decimal' : undefined}
          step={f.step}
          min={f.min}
          max={f.max}
          value={value ?? ''}
          placeholder={f.placeholder}
          list={f.list ? `${id}-list` : undefined}
          onChange={(e) => onChange(e.target.value)}
          className={cx(inputCls, border, f.type === 'number' && 'num')}
          aria-invalid={!!error}
        />
        {f.list && (
          <datalist id={`${id}-list`}>
            {f.list.map((o) => (
              <option key={o} value={o} />
            ))}
          </datalist>
        )}
      </>
    )
  }
  return (
    <div className={cx('min-w-0', span)}>
      <label htmlFor={id} className="mb-1 block text-xs font-medium text-muted">
        {f.label}
        {f.required && <span className="text-neg"> *</span>}
      </label>
      {control}
      {error ? <p className="mt-1 text-xs text-neg">{error}</p> : f.help && <p className="mt-1 text-xs text-faint">{f.help}</p>}
    </div>
  )
}

export function ConfirmDialog({ open, title, message, onCancel, onConfirm, confirmLabel = 'Delete' }) {
  const [busy, setBusy] = useState(false)
  return (
    <Modal
      open={open}
      title={title}
      onClose={onCancel}
      footer={
        <>
          <Button variant="ghost" onClick={onCancel}>
            Cancel
          </Button>
          <Button
            variant="danger"
            loading={busy}
            onClick={async () => {
              setBusy(true)
              try {
                await onConfirm()
              } finally {
                setBusy(false)
              }
            }}
          >
            {confirmLabel}
          </Button>
        </>
      }
    >
      <p className="text-sm text-muted">{message}</p>
    </Modal>
  )
}
