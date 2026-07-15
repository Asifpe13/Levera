import { useCallback, useEffect, useState } from 'react'
import {
  ActivityIndicator,
  FlatList,
  Linking,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native'
import NetInfo from '@react-native-community/netinfo'

import { getProperties, type Property } from '@/src/api'
import { useAuth } from '@/src/auth'
import { buildCacheKey, readCachedProperties, writeCachedProperties } from '@/src/offline'

function PropertyRow({ item }: { item: Property }) {
  return (
    <Pressable
      style={styles.card}
      onPress={() => item.listing_url && Linking.openURL(item.listing_url)}
    >
      <View style={styles.row}>
        <Text style={styles.city}>{item.city}</Text>
        <Text style={styles.price}>₪{item.price?.toLocaleString('he-IL')}</Text>
      </View>
      <Text style={styles.meta}>
        {item.rooms ? `${item.rooms} חד׳ · ` : ''}
        {item.deal_type === 'rent' ? 'שכירות' : 'מכירה'}
        {item.ai_score != null ? ` · ציון ${item.ai_score}` : ''}
      </Text>
      {item.ai_summary ? <Text style={styles.summary} numberOfLines={2}>{item.ai_summary}</Text> : null}
    </Pressable>
  )
}

export default function DealsScreen() {
  const { user } = useAuth()
  const [items, setItems] = useState<Property[]>([])
  const [loading, setLoading] = useState(true)
  const [fromCache, setFromCache] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  const load = useCallback(async () => {
    if (!user) return
    const key = buildCacheKey(user.email, 'latest')
    const net = await NetInfo.fetch()

    if (!net.isConnected) {
      const cached = await readCachedProperties(key)
      setItems(cached || [])
      setFromCache(true)
      setLoading(false)
      return
    }

    try {
      const list = await getProperties({ view: 'latest', limit: 50 })
      setItems(list)
      setFromCache(false)
      await writeCachedProperties(key, list)
    } catch {
      const cached = await readCachedProperties(key)
      setItems(cached || [])
      setFromCache(true)
    } finally {
      setLoading(false)
    }
  }, [user])

  useEffect(() => {
    load()
  }, [load])

  async function onRefresh() {
    setRefreshing(true)
    await load()
    setRefreshing(false)
  }

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#0d9488" />
      </View>
    )
  }

  return (
    <View style={styles.container}>
      {fromCache && (
        <View style={styles.offlineBanner}>
          <Text style={styles.offlineText}>מציג דירות שמורות — אין חיבור / שגיאת שרת</Text>
        </View>
      )}
      <FlatList
        data={items}
        keyExtractor={(p, i) => p.id || String(i)}
        renderItem={({ item }) => <PropertyRow item={item} />}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#0d9488" />}
        ListEmptyComponent={
          <Text style={styles.empty}>אין דירות עדיין — הרץ סריקה מהווב או המתן לסריקה אוטומטית</Text>
        }
        contentContainerStyle={items.length === 0 ? styles.center : undefined}
      />
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8fafc' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  offlineBanner: { backgroundColor: '#fef3c7', padding: 10 },
  offlineText: { textAlign: 'center', color: '#92400e', fontSize: 12, fontWeight: '600' },
  card: {
    backgroundColor: '#fff',
    marginHorizontal: 12,
    marginVertical: 6,
    padding: 14,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  row: { flexDirection: 'row-reverse', justifyContent: 'space-between', marginBottom: 4 },
  city: { fontSize: 16, fontWeight: '700', color: '#0f172a' },
  price: { fontSize: 15, fontWeight: '700', color: '#0d9488' },
  meta: { fontSize: 13, color: '#64748b', textAlign: 'right' },
  summary: { fontSize: 12, color: '#475569', marginTop: 6, textAlign: 'right' },
  empty: { textAlign: 'center', color: '#64748b', fontSize: 14, lineHeight: 22 },
})
