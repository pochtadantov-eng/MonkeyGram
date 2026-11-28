import { useSyncExternalStore } from 'react'
import { getVisualSettings, subscribeVisual } from '../store/visualStore'

export function useVisual() {
  return useSyncExternalStore(subscribeVisual, getVisualSettings, getVisualSettings)
}
