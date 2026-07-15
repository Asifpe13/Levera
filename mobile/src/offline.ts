import AsyncStorage from '@react-native-async-storage/async-storage'
import type { Property } from './api'

const PREFIX = 'levera:properties:'

export async function readCachedProperties(key: string): Promise<Property[] | null> {
  const raw = await AsyncStorage.getItem(PREFIX + key)
  if (!raw) return null
  try {
    return JSON.parse(raw) as Property[]
  } catch {
    return null
  }
}

export async function writeCachedProperties(key: string, data: Property[]): Promise<void> {
  await AsyncStorage.setItem(PREFIX + key, JSON.stringify(data))
}

export function buildCacheKey(email: string, view = 'latest') {
  return `${email}:${view}`
}
