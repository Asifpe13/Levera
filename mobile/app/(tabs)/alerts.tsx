import { useCallback, useEffect, useState } from 'react'
import { ActivityIndicator, FlatList, RefreshControl, StyleSheet, Text, View } from 'react-native'

import { getNotifications, type AppNotification } from '@/src/api'

export default function AlertsScreen() {
  const [items, setItems] = useState<AppNotification[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const load = useCallback(async () => {
    try {
      setItems(await getNotifications(100))
    } catch {
      setItems([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#0d9488" />
      </View>
    )
  }

  return (
    <FlatList
      style={styles.list}
      data={items}
      keyExtractor={(n) => n.id}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={async () => {
            setRefreshing(true)
            await load()
            setRefreshing(false)
          }}
          tintColor="#0d9488"
        />
      }
      ListEmptyComponent={<Text style={styles.empty}>אין התראות עדיין</Text>}
      renderItem={({ item }) => (
        <View style={[styles.card, !item.read && styles.unread]}>
          <Text style={styles.title}>{item.title}</Text>
          <Text style={styles.message}>{item.message}</Text>
          <Text style={styles.time}>
            {new Date(item.created_at).toLocaleString('he-IL')}
          </Text>
        </View>
      )}
    />
  )
}

const styles = StyleSheet.create({
  list: { flex: 1, backgroundColor: '#f8fafc' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  card: {
    backgroundColor: '#fff',
    marginHorizontal: 12,
    marginVertical: 6,
    padding: 14,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  unread: { borderRightWidth: 4, borderRightColor: '#0d9488', backgroundColor: '#f0fdfa' },
  title: { fontSize: 15, fontWeight: '700', textAlign: 'right', color: '#0f172a' },
  message: { fontSize: 13, color: '#475569', textAlign: 'right', marginTop: 4 },
  time: { fontSize: 11, color: '#94a3b8', textAlign: 'left', marginTop: 8 },
  empty: { textAlign: 'center', marginTop: 40, color: '#64748b' },
})
