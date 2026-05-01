import { useEffect, useMemo, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

const draftStorageKey = 'expense-form-draft-v1'
const pendingStorageKey = 'expense-form-pending-v1'
const currencyFormatter = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 2,
})

const emptyForm = {
  amount: '',
  category: '',
  description: '',
  date: '',
}

function createIdempotencyKey() {
  if (window.crypto?.randomUUID) {
    return window.crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function readStoredJson(key) {
  try {
    const value = window.localStorage.getItem(key)
    return value ? JSON.parse(value) : null
  } catch {
    return null
  }
}

function formatExpenseAmount(amount) {
  return currencyFormatter.format(Number(amount))
}

function parseVisibleTotal(expenses) {
  return expenses.reduce((sum, expense) => sum + Number(expense.amount), 0)
}

export default function App() {
  const [form, setForm] = useState(emptyForm)
  const [expenses, setExpenses] = useState([])
  const [filterCategory, setFilterCategory] = useState('all')
  const [sortOrder, setSortOrder] = useState('date_desc')
  const [loading, setLoading] = useState(true)
  const [loadingMessage, setLoadingMessage] = useState('Loading expenses...')
  const [error, setError] = useState('')
  const [submitError, setSubmitError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    const storedForm = readStoredJson(draftStorageKey)
    if (storedForm) {
      setForm((current) => ({ ...current, ...storedForm }))
    }
  }, [])

  useEffect(() => {
    window.localStorage.setItem(draftStorageKey, JSON.stringify(form))
  }, [form])

  useEffect(() => {
    const controller = new AbortController()

    async function loadExpenses() {
      setLoading(true)
      setError('')

      try {
        const params = new URLSearchParams()
        if (filterCategory !== 'all') {
          params.set('category', filterCategory)
        }
        params.set('sort', 'date_desc')

        const response = await fetch(`${API_BASE}/expenses?${params.toString()}`, {
          signal: controller.signal,
        })

        if (!response.ok) {
          throw new Error('Unable to load expenses right now.')
        }

        const data = await response.json()
        setExpenses(Array.isArray(data.expenses) ? data.expenses : [])
      } catch (loadError) {
        if (loadError.name !== 'AbortError') {
          setError(loadError.message || 'Unable to load expenses right now.')
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }

    loadExpenses()
    return () => controller.abort()
  }, [filterCategory])

  const categories = useMemo(() => {
    const found = new Set(expenses.map((expense) => expense.category))
    if (filterCategory !== 'all') {
      found.add(filterCategory)
    }
    return Array.from(found).sort((left, right) => left.localeCompare(right))
  }, [expenses, filterCategory])

  const visibleExpenses = useMemo(() => {
    const list = [...expenses]
    if (sortOrder === 'date_asc') {
      list.reverse()
    }
    return list
  }, [expenses, sortOrder])

  const visibleTotal = useMemo(() => parseVisibleTotal(visibleExpenses), [visibleExpenses])

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitError('')

    const nextForm = {
      amount: form.amount.trim(),
      category: form.category.trim(),
      description: form.description.trim(),
      date: form.date,
    }

    if (!nextForm.amount || !nextForm.category || !nextForm.description || !nextForm.date) {
      setSubmitError('Please fill in amount, category, description, and date.')
      return
    }

    const parsedAmount = Number(nextForm.amount)
    if (!Number.isFinite(parsedAmount) || parsedAmount <= 0) {
      setSubmitError('Amount must be a positive number.')
      return
    }

    const storedPending = readStoredJson(pendingStorageKey)
    const samePendingSubmission =
      storedPending && JSON.stringify(storedPending.payload) === JSON.stringify(nextForm)
    const idempotencyKey = samePendingSubmission
      ? storedPending.idempotencyKey
      : createIdempotencyKey()

    const payload = {
      amount: nextForm.amount,
      category: nextForm.category,
      description: nextForm.description,
      date: nextForm.date,
    }

    setSubmitting(true)
    window.localStorage.setItem(
      pendingStorageKey,
      JSON.stringify({ idempotencyKey, payload }),
    )

    try {
      const response = await fetch(`${API_BASE}/expenses`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Idempotency-Key': idempotencyKey,
        },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const body = await response.json().catch(() => null)
        const message =
          body?.errors
            ? Object.values(body.errors).join(' ')
            : body?.detail || 'Unable to save the expense.'
        throw new Error(message)
      }

      setForm(emptyForm)
      window.localStorage.removeItem(pendingStorageKey)
      window.localStorage.removeItem(draftStorageKey)
      await refreshExpenses()
    } catch (submitFailure) {
      setSubmitError(submitFailure.message || 'Unable to save the expense.')
    } finally {
      setSubmitting(false)
    }
  }

  async function refreshExpenses() {
    const params = new URLSearchParams()
    if (filterCategory !== 'all') {
      params.set('category', filterCategory)
    }
    params.set('sort', 'date_desc')

    const response = await fetch(`${API_BASE}/expenses?${params.toString()}`)
    if (!response.ok) {
      throw new Error('Expense saved, but the latest list could not be loaded.')
    }
    const data = await response.json()
    setExpenses(Array.isArray(data.expenses) ? data.expenses : [])
  }

  return (
    <main className="app-shell">
      <section className="hero-card">
        <div className="hero-content">
          <p className="eyebrow">💰 Personal Finance Tracker</p>
          <h1>Smart Expense Tracking</h1>
        </div>
      </section>

      <section className="content-grid">
        <form className="panel form-panel" onSubmit={handleSubmit}>
          <div className="panel-header">
            <div className="header-icon">➕</div>
            <div>
              <h2>Add New Expense</h2>
              {/* <p>Fill in the details below to track a new expense</p> */}
            </div>
          </div>

          <div className="field-grid">
            <label className="form-field">
              <span className="field-label">Amount (₹)</span>
              <div className="input-wrapper">
                <span className="currency-symbol">₹</span>
                <input
                  type="number"
                  inputMode="decimal"
                  min="0.00"
                  step="1"
                  value={form.amount}
                  onChange={(event) => setForm((current) => ({ ...current, amount: event.target.value }))}
                  placeholder="0.00"
                  required
                />
              </div>
            </label>
            <label className="form-field">
              <span className="field-label">Category</span>
              <div className="input-wrapper">
                <span className="field-icon">📂</span>
                <input
                  type="text"
                  value={form.category}
                  onChange={(event) => setForm((current) => ({ ...current, category: event.target.value }))}
                  placeholder="Food, Travel, Bills, Shopping..."
                  required
                />
              </div>
            </label>
            <label className="form-field wide-field">
              <span className="field-label">Description</span>
              <textarea
                value={form.description}
                onChange={(event) =>
                  setForm((current) => ({ ...current, description: event.target.value }))
                }
                placeholder="What was this expense for? (e.g., Lunch at restaurant, Taxi to airport)"
                rows="3"
                required
              />
            </label>
            <label className="form-field">
              <span className="field-label">Date</span>
              <div className="input-wrapper">
                <span className="field-icon">📅</span>
                <input
                  type="date"
                  value={form.date}
                  onChange={(event) => setForm((current) => ({ ...current, date: event.target.value }))}
                  required
                />
              </div>
            </label>
          </div>

          {submitError ? <div className="alert error">⚠️ {submitError}</div> : null}

          <button className="primary-button" type="submit" disabled={submitting}>
            {submitting ? (
              <>
                <span className="button-spinner"></span>
                Saving...
              </>
            ) : (
              <>✨ Save Expense</>
            )}
          </button>
        </form>

        <section className="panel list-panel">
          <div className="panel-header">
            <div className="header-icon">📊</div>
            <div>
              <h2>Your Expenses</h2>
              {/* <p>View and manage all your tracked expenses</p> */}
            </div>
          </div>

          <div className="controls-section">
            <div className="control-group">
              <label>
                <span className="control-label">Filter by Category</span>
                <select
                  className="control-select"
                  value={filterCategory}
                  onChange={(event) => setFilterCategory(event.target.value)}
                >
                  <option value="all">📌 All Categories</option>
                  {categories.map((category) => (
                    <option key={category} value={category}>
                      {category}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div className="control-group">
              <label>
                <span className="control-label">Sort By</span>
                <select className="control-select" value={sortOrder} onChange={(event) => setSortOrder(event.target.value)}>
                  <option value="date_desc">📥 Newest First</option>
                  <option value="date_asc">📤 Oldest First</option>
                </select>
              </label>
            </div>
          </div>

          {loading ? <div className="state-box loading">⏳ {loadingMessage}</div> : null}
          {!loading && error ? <div className="alert error">❌ {error}</div> : null}

          {!loading && !error ? (
            visibleExpenses.length === 0 ? (
              <div className="state-box empty">
                <div className="empty-icon">🎯</div>
                <div>No expenses found</div>
                <div className="empty-hint">Add your first expense to get started!</div>
              </div>
            ) : (
              <div className="table-wrap">
                <table className="expenses-table">
                  <thead>
                    <tr>
                      <th className="date-column">📅 Date</th>
                      <th className="category-column">📂 Category</th>
                      <th className="description-column">📝 Description</th>
                      <th className="amount-column">💵 Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {visibleExpenses.map((expense, index) => (
                      <tr key={expense.id} className={index % 2 === 0 ? 'even-row' : 'odd-row'}>
                        <td className="date-column">{expense.date}</td>
                        <td className="category-column">
                          <span className="category-badge">{expense.category}</span>
                        </td>
                        <td className="description-column">{expense.description}</td>
                        <td className="amount-column">
                          <span className="amount-value">{formatExpenseAmount(expense.amount)}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          ) : null}

          <div className="summary-pill summary-pill-bottom">
            <div className="summary-label">Total Expenses</div>
            <div className="summary-amount">{currencyFormatter.format(visibleTotal)}</div>
          </div>
        </section>
      </section>
    </main>
  )
}
