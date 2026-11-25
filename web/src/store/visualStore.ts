export type Currency = 'stars' | 'ton'

export type HistoryEntry = {
  id: string
  currency: Currency
  direction: 'in' | 'out'
  amount: number
  title: string
  subtitle?: string
  at: number
}

export type VisualSettings = {
  visualGiftsEnabled: boolean
  visualBalanceEnabled: boolean
  starsBalance: number
  tonBalance: number
  history: HistoryEntry[]
}

const STORAGE_KEY = 'monkeygram-visual-v1'

const DEFAULTS: VisualSettings = {
  visualGiftsEnabled: false,
  visualBalanceEnabled: false,
  starsBalance: 0,
  tonBalance: 0,
  history: [],
}

function load(): VisualSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { ...DEFAULTS, history: [] }
    const parsed = JSON.parse(raw) as Partial<VisualSettings>
    return {
      visualGiftsEnabled: Boolean(parsed.visualGiftsEnabled),
      visualBalanceEnabled: Boolean(parsed.visualBalanceEnabled),
      starsBalance: Number(parsed.starsBalance) || 0,
      tonBalance: Number(parsed.tonBalance) || 0,
      history: Array.isArray(parsed.history) ? parsed.history : [],
    }
  } catch {
    return { ...DEFAULTS, history: [] }
  }
}

function save(state: VisualSettings) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
}

type Listener = (state: VisualSettings) => void

let state = load()
const listeners = new Set<Listener>()

function emit() {
  save(state)
  listeners.forEach((l) => l(state))
}

export function getVisualSettings(): VisualSettings {
  return state
}

export function subscribeVisual(listener: Listener): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function setVisualGiftsEnabled(enabled: boolean) {
  state = { ...state, visualGiftsEnabled: enabled }
  emit()
}

export function setVisualBalanceEnabled(enabled: boolean) {
  state = { ...state, visualBalanceEnabled: enabled }
  emit()
}

export function saveBalances(stars: number, ton: number) {
  const nextStars = Math.max(0, Number.isFinite(stars) ? stars : 0)
  const nextTon = Math.max(0, Number.isFinite(ton) ? ton : 0)
  const entries: HistoryEntry[] = []
  const now = Date.now()

  if (nextStars > state.starsBalance) {
    entries.push({
      id: `in-stars-${now}`,
      currency: 'stars',
      direction: 'in',
      amount: nextStars - state.starsBalance,
      title: 'Пополнение Stars',
      subtitle: 'Визуальный баланс',
      at: now,
    })
  } else if (nextStars < state.starsBalance) {
    entries.push({
      id: `adj-stars-${now}`,
      currency: 'stars',
      direction: 'out',
      amount: state.starsBalance - nextStars,
      title: 'Корректировка Stars',
      subtitle: 'Визуальный баланс',
      at: now,
    })
  }

  if (nextTon > state.tonBalance) {
    entries.push({
      id: `in-ton-${now}`,
      currency: 'ton',
      direction: 'in',
      amount: nextTon - state.tonBalance,
      title: 'Пополнение TON',
      subtitle: 'Визуальный баланс',
      at: now + 1,
    })
  } else if (nextTon < state.tonBalance) {
    entries.push({
      id: `adj-ton-${now}`,
      currency: 'ton',
      direction: 'out',
      amount: state.tonBalance - nextTon,
      title: 'Корректировка TON',
      subtitle: 'Визуальный баланс',
      at: now + 1,
    })
  }

  state = {
    ...state,
    starsBalance: nextStars,
    tonBalance: nextTon,
    history: [...entries, ...state.history].slice(0, 200),
  }
  emit()
}

export function spendVisual(
  currency: Currency,
  amount: number,
  title: string,
  subtitle?: string,
): { ok: true } | { ok: false; reason: string } {
  if (!state.visualBalanceEnabled) {
    return { ok: false, reason: 'Визуальный баланс выключен' }
  }
  if (amount <= 0) return { ok: false, reason: 'Некорректная сумма' }

  const entry: HistoryEntry = {
    id: `out-${currency}-${Date.now()}`,
    currency,
    direction: 'out',
    amount,
    title,
    subtitle,
    at: Date.now(),
  }

  if (currency === 'stars') {
    if (state.starsBalance < amount) return { ok: false, reason: 'Недостаточно Stars' }
    state = {
      ...state,
      starsBalance: +(state.starsBalance - amount).toFixed(2),
      history: [entry, ...state.history].slice(0, 200),
    }
  } else {
    if (state.tonBalance < amount) return { ok: false, reason: 'Недостаточно TON' }
    state = {
      ...state,
      tonBalance: +(state.tonBalance - amount).toFixed(4),
      history: [entry, ...state.history].slice(0, 200),
    }
  }
  emit()
  return { ok: true }
}

export function historyFor(currency: Currency): HistoryEntry[] {
  return state.history.filter((h) => h.currency === currency)
}
