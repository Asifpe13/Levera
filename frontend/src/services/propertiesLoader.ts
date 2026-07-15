import { getProperties, type Property } from '../api'
import {
  buildCacheKey,
  isOnline,
  readPropertyCache,
  writePropertyCache,
} from './propertyCache'

export interface LoadPropertiesResult {
  properties: Property[]
  fromCache: boolean
  fetchedAt: number | null
}

export async function loadPropertiesWithCache(
  email: string,
  params?: {
    deal_type?: string
    city?: string
    limit?: number
    view?: 'latest' | 'all'
  },
): Promise<LoadPropertiesResult> {
  const key = buildCacheKey({ email, ...params })
  const cached = await readPropertyCache(key)

  if (!isOnline()) {
    if (cached) {
      return { properties: cached.data, fromCache: true, fetchedAt: cached.fetchedAt }
    }
    throw new Error('אין חיבור לאינטרנט ואין נתונים שמורים')
  }

  try {
    const list = await getProperties(params)
    await writePropertyCache(key, list)
    return { properties: list, fromCache: false, fetchedAt: Date.now() }
  } catch (err) {
    if (cached) {
      return { properties: cached.data, fromCache: true, fetchedAt: cached.fetchedAt }
    }
    throw err
  }
}
