import { openDB, type IDBPDatabase } from 'idb'
import type { Property } from '../api'

const DB_NAME = 'levera-offline'
const DB_VERSION = 1
const STORE = 'properties'

export interface CachedPropertyList {
  key: string
  data: Property[]
  fetchedAt: number
}

let dbPromise: Promise<IDBPDatabase> | null = null

function getDb() {
  if (!dbPromise) {
    dbPromise = openDB(DB_NAME, DB_VERSION, {
      upgrade(db) {
        if (!db.objectStoreNames.contains(STORE)) {
          db.createObjectStore(STORE, { keyPath: 'key' })
        }
      },
    })
  }
  return dbPromise
}

export function buildCacheKey(params: {
  email: string
  view?: string
  deal_type?: string
  city?: string
  limit?: number
}): string {
  return [
    params.email,
    params.view || 'all',
    params.deal_type || '',
    params.city || '',
    String(params.limit || 50),
  ].join(':')
}

export async function readPropertyCache(key: string): Promise<CachedPropertyList | null> {
  const db = await getDb()
  return (await db.get(STORE, key)) ?? null
}

export async function writePropertyCache(key: string, data: Property[]): Promise<void> {
  const db = await getDb()
  await db.put(STORE, { key, data, fetchedAt: Date.now() } satisfies CachedPropertyList)
}

export async function clearPropertyCache(): Promise<void> {
  const db = await getDb()
  await db.clear(STORE)
}

export function isOnline(): boolean {
  return typeof navigator === 'undefined' ? true : navigator.onLine
}
