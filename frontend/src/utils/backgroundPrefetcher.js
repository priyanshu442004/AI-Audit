import { useStore } from '../store'
import {
  fetchPriceVarianceSame,
  fetchPriceVarianceCross,
  fetchPaymentAgingDomestic,
  fetchPaymentAgingForeign,
  fetchPaymentAgingRelated,
  fetchPaymentAgingMsme,
  fetchVendorMasterNew,
  fetchThreeWayMatching
} from '../api'

export const PREFETCH_TASKS = [
  { key: 'priceVarianceSame', fetchFn: fetchPriceVarianceSame, setter: 'setPriceVarianceSame' },
  { key: 'priceVarianceCross', fetchFn: fetchPriceVarianceCross, setter: 'setPriceVarianceCross' },
  { key: 'paymentAgingDomestic', fetchFn: fetchPaymentAgingDomestic, setter: 'setPaymentAgingDomestic' },
  { key: 'paymentAgingForeign', fetchFn: fetchPaymentAgingForeign, setter: 'setPaymentAgingForeign' },
  { key: 'paymentAgingRelated', fetchFn: fetchPaymentAgingRelated, setter: 'setPaymentAgingRelated' },
  { key: 'paymentAgingMsme', fetchFn: fetchPaymentAgingMsme, setter: 'setPaymentAgingMsme' },
  { key: 'vendorMasterNew', fetchFn: fetchVendorMasterNew, setter: 'setVendorMasterNew' },
  { key: 'threeWayMatching', fetchFn: fetchThreeWayMatching, setter: 'setThreeWayMatching' },
]

let activePrefetchPromise = null

export async function startPrefetching() {
  if (activePrefetchPromise) return activePrefetchPromise

  activePrefetchPromise = (async () => {
    try {
      for (const task of PREFETCH_TASKS) {
        // Always get the latest store state to prevent stale closures
        const state = useStore.getState()
        const currentState = (state.backgroundStates || {})[task.key]
        
        if (currentState === 'loading' || currentState === 'success') {
          continue
        }

        // If store already has the data, mark success
        if (state[task.key]) {
          state.setBackgroundState(task.key, 'success')
          continue
        }

        state.setBackgroundState(task.key, 'loading')
        try {
          const data = await task.fetchFn()
          const setFn = state[task.setter]
          if (setFn) {
            setFn(data)
          }
          state.setBackgroundState(task.key, 'success')
        } catch (err) {
          console.error(`Prefetch failed for ${task.key}:`, err)
          state.setBackgroundState(task.key, 'error')
        }
      }
    } finally {
      activePrefetchPromise = null
    }
  })()

  return activePrefetchPromise
}
