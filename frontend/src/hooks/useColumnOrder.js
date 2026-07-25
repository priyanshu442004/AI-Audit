import { useState, useCallback, useEffect, useMemo } from 'react'

/**
 * Manages a user-reorderable column order for a table, persisted to localStorage.
 * `defaultCols` should be the full, stable list of columns for the table (order-independent
 * subsets like group/tab filters should be derived by filtering the returned `order`).
 */
export default function useColumnOrder(storageKey, defaultCols) {
  const key = `colOrder:${storageKey}`
  const defaultKey = defaultCols.join('|')

  const [order, setOrder] = useState(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(key) || 'null')
      if (Array.isArray(saved)) {
        const kept = saved.filter(c => defaultCols.includes(c))
        const missing = defaultCols.filter(c => !kept.includes(c))
        return [...kept, ...missing]
      }
    } catch {
      // ignore malformed storage
    }
    return defaultCols
  })

  // Keep order in sync if the underlying column set changes (new/removed cols),
  // while preserving whatever order the user already chose.
  useEffect(() => {
    setOrder(prev => {
      const kept = prev.filter(c => defaultCols.includes(c))
      const missing = defaultCols.filter(c => !kept.includes(c))
      if (kept.length === prev.length && missing.length === 0) return prev
      return [...kept, ...missing]
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [defaultKey])

  const moveColumn = useCallback((fromCol, toCol) => {
    setOrder(prev => {
      if (fromCol === toCol) return prev
      const fromIdx = prev.indexOf(fromCol)
      const toIdx = prev.indexOf(toCol)
      if (fromIdx === -1 || toIdx === -1) return prev
      const next = [...prev]
      next.splice(fromIdx, 1)
      next.splice(next.indexOf(toCol) + (fromIdx < toIdx ? 1 : 0), 0, fromCol)
      try { localStorage.setItem(key, JSON.stringify(next)) } catch { /* ignore quota errors */ }
      return next
    })
  }, [key])

  const resetOrder = useCallback(() => {
    setOrder(defaultCols)
    try { localStorage.removeItem(key) } catch { /* ignore */ }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, defaultKey])

  const isCustomOrder = useMemo(() => order.join('|') !== defaultKey, [order, defaultKey])

  return { order, moveColumn, resetOrder, isCustomOrder }
}
