import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Linking,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import NetInfo from '@react-native-community/netinfo'

import {
  getProperties,
  getScanStatus,
  requestWeeklyReport,
  startScan,
  type Property,
  type ScanStatus,
} from '@/src/api'
import { useAuth } from '@/src/auth'
import { buildCacheKey, readCachedProperties, writeCachedProperties } from '@/src/offline'

type ViewMode = 'latest' | 'all'
type DealFilter = 'all' | 'sale' | 'rent'

function PropertyCard({ item }: { item: Property }) {
  const [expanded, setExpanded] = useState(false)
  const score = Math.round(item.ai_score ?? 0)

  return (
    <View style={styles.propertyCard}>
      <Pressable style={styles.propertyMain} onPress={() => setExpanded((current) => !current)}>
        <View style={styles.scoreWrap}>
          <Text style={styles.score}>{score || '—'}</Text>
          <Text style={styles.scoreLabel}>ציון</Text>
        </View>
        <View style={styles.propertyContent}>
          <View style={styles.row}>
            <Text style={styles.city}>{item.city}</Text>
            <Text style={styles.price}>₪{item.price.toLocaleString('he-IL')}</Text>
          </View>
          <Text style={styles.meta}>
            {[item.neighborhood, item.rooms ? `${item.rooms} חד׳` : '', item.size_sqm ? `${item.size_sqm} מ״ר` : '']
              .filter(Boolean)
              .join(' · ')}
          </Text>
          {item.value_label ? <Text style={styles.valueLabel}>{item.value_label}</Text> : null}
        </View>
        <Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={18} color="#64748b" />
      </Pressable>

      {expanded && (
        <View style={styles.propertyDetails}>
          {item.ai_summary ? <Text style={styles.summary}>{item.ai_summary}</Text> : null}
          {item.monthly_repayment ? (
            <View style={styles.mortgageRow}>
              <Ionicons name="wallet-outline" size={17} color="#0f766e" />
              <Text style={styles.mortgageText}>
                החזר חודשי משוער: ₪{Math.round(item.monthly_repayment).toLocaleString('he-IL')}
              </Text>
            </View>
          ) : null}
          {item.market_summary_text ? <Text style={styles.marketText}>{item.market_summary_text}</Text> : null}
          {item.listing_url ? (
            <Pressable style={styles.listingButton} onPress={() => Linking.openURL(item.listing_url!)}>
              <Text style={styles.listingButtonText}>צפה במודעה המקורית</Text>
              <Ionicons name="open-outline" size={16} color="#fff" />
            </Pressable>
          ) : null}
        </View>
      )}
    </View>
  )
}

function ScanPanel({ status, scanning, onScan, onReport }: {
  status: ScanStatus | null
  scanning: boolean
  onScan: () => void
  onReport: () => void
}) {
  const progress = Math.max(0, Math.min(status?.progress ?? (scanning ? 5 : 0), 100))

  return (
    <View style={styles.scanCard}>
      <View style={styles.scanHeader}>
        <View>
          <Text style={styles.scanEyebrow}>סוכן Levera</Text>
          <Text style={styles.scanTitle}>{scanning ? 'הסוכן עובד עבורך' : 'מצא את ההזדמנות הבאה שלך'}</Text>
        </View>
        <View style={[styles.statusDot, scanning && styles.statusDotActive]} />
      </View>

      {scanning || status?.finished ? (
        <View style={styles.progressSection}>
          <View style={styles.progressTrack}>
            <View style={[styles.progressValue, { width: `${progress}%` }]} />
          </View>
          <Text style={styles.progressText}>{status?.message || 'מכין את הסריקה...'}</Text>
          {status?.finished ? (
            <Text style={styles.resultText}>
              נסרקו {status.total_found} דירות · נמצאו {status.total_matches} התאמות
            </Text>
          ) : null}
        </View>
      ) : (
        <Text style={styles.scanDescription}>סריקה חכמה לפי התקציב, הערים והפרופיל הפיננסי שלך.</Text>
      )}

      <View style={styles.scanActions}>
        <Pressable style={[styles.scanButton, scanning && styles.scanButtonDisabled]} onPress={onScan} disabled={scanning}>
          {scanning ? <ActivityIndicator color="#0f766e" /> : <Ionicons name="search" size={18} color="#0f766e" />}
          <Text style={styles.scanButtonText}>{scanning ? 'הסריקה מתבצעת' : 'התחל סריקה'}</Text>
        </Pressable>
        <Pressable style={styles.reportButton} onPress={onReport} disabled={scanning}>
          <Ionicons name="document-text-outline" size={18} color="#d1fae5" />
        </Pressable>
      </View>
    </View>
  )
}

export default function DealsScreen() {
  const { user } = useAuth()
  const [items, setItems] = useState<Property[]>([])
  const [loading, setLoading] = useState(true)
  const [fromCache, setFromCache] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [view, setView] = useState<ViewMode>('latest')
  const [dealFilter, setDealFilter] = useState<DealFilter>('all')
  const [cityFilter, setCityFilter] = useState('הכל')
  const [scanStatus, setScanStatus] = useState<ScanStatus | null>(null)
  const [scanning, setScanning] = useState(false)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const load = useCallback(async () => {
    if (!user) return
    const key = buildCacheKey(user.email, `${view}:${dealFilter}:${cityFilter}`)
    const net = await NetInfo.fetch()

    if (!net.isConnected) {
      const cached = await readCachedProperties(key)
      setItems(cached || [])
      setFromCache(true)
      setLoading(false)
      return
    }

    try {
      const list = await getProperties({
        view,
        limit: 50,
        deal_type: dealFilter === 'all' ? undefined : dealFilter,
        city: cityFilter === 'הכל' ? undefined : cityFilter,
      })
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
  }, [user, view, dealFilter, cityFilter])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => () => {
    if (pollRef.current) clearInterval(pollRef.current)
  }, [])

  const cities = useMemo(
    () => ['הכל', ...Array.from(new Set(items.map((item) => item.city).filter(Boolean))).sort()],
    [items],
  )

  function beginPolling() {
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = setInterval(async () => {
      try {
        const next = await getScanStatus()
        setScanStatus(next)
        if (next.finished && !next.running) {
          if (pollRef.current) clearInterval(pollRef.current)
          pollRef.current = null
          setScanning(false)
          load()
        }
      } catch {}
    }, 2_000)
  }

  async function handleScan() {
    if (scanning) return
    setScanning(true)
    setScanStatus({
      running: true,
      finished: false,
      message: 'מחבר את הסוכן לשרת...',
      total_found: 0,
      total_matches: 0,
      log: [],
      rejections: {},
      progress: 5,
    })
    try {
      await startScan()
      beginPolling()
    } catch (error) {
      const message = error instanceof Error ? error.message : ''
      if (message.includes('זמן') || message.toLowerCase().includes('timeout')) {
        beginPolling()
        return
      }
      setScanning(false)
      setScanStatus(null)
      Alert.alert('לא ניתן להתחיל סריקה', message || 'בדוק את החיבור לשרת ונסה שוב')
    }
  }

  async function handleReport() {
    try {
      const result = await requestWeeklyReport()
      Alert.alert(
        result.ok ? 'הדוח נשלח' : 'לא ניתן היה לשלוח דוח',
        result.ok ? `הדוח השבועי נשלח למייל עם ${result.properties_count} דירות.` : result.message,
      )
    } catch (error) {
      Alert.alert('לא ניתן היה להפיק דוח', error instanceof Error ? error.message : 'נסה שוב מאוחר יותר')
    }
  }

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
        renderItem={({ item }) => <PropertyCard item={item} />}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#0d9488" />}
        ListHeaderComponent={
          <View style={styles.listHeader}>
            <View style={styles.welcome}>
              <View>
                <Text style={styles.welcomeOverline}>בוקר טוב, {user?.name?.split(' ')[0]}</Text>
                <Text style={styles.welcomeTitle}>הדירות שלך</Text>
              </View>
              <View style={styles.avatar}><Text style={styles.avatarText}>{user?.name?.[0] || 'L'}</Text></View>
            </View>
            <ScanPanel status={scanStatus} scanning={scanning} onScan={handleScan} onReport={handleReport} />
            <View style={styles.metrics}>
              <View style={styles.metric}><Text style={styles.metricValue}>{user?.target_cities.length || 0}</Text><Text style={styles.metricLabel}>ערים במעקב</Text></View>
              <View style={styles.metricDivider} />
              <View style={styles.metric}><Text style={styles.metricValue}>₪{Math.round((user?.monthly_income || 0) * (user?.max_repayment_ratio || 0)).toLocaleString('he-IL')}</Text><Text style={styles.metricLabel}>החזר חודשי</Text></View>
              <View style={styles.metricDivider} />
              <View style={styles.metric}><Text style={styles.metricValue}>₪{Math.round((user?.equity || 0) / 1000)}K</Text><Text style={styles.metricLabel}>הון עצמי</Text></View>
            </View>
            <View style={styles.sectionHeader}><Text style={styles.sectionTitle}>הזדמנויות עבורך</Text><Text style={styles.sectionCount}>{items.length} דירות</Text></View>
            <View style={styles.segmented}>
              {([{ key: 'latest', label: 'סריקה אחרונה' }, { key: 'all', label: 'כל הדירות' }] as const).map((option) => (
                <Pressable key={option.key} onPress={() => setView(option.key)} style={[styles.segment, view === option.key && styles.segmentActive]}>
                  <Text style={[styles.segmentText, view === option.key && styles.segmentTextActive]}>{option.label}</Text>
                </Pressable>
              ))}
            </View>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chips}>
              {([{ key: 'all', label: 'הכל' }, { key: 'sale', label: 'מכירה' }, { key: 'rent', label: 'שכירות' }] as const).map((option) => (
                <Pressable key={option.key} onPress={() => setDealFilter(option.key)} style={[styles.chip, dealFilter === option.key && styles.chipActive]}>
                  <Text style={[styles.chipText, dealFilter === option.key && styles.chipTextActive]}>{option.label}</Text>
                </Pressable>
              ))}
              {cities.map((city) => city !== 'הכל' ? (
                <Pressable key={city} onPress={() => setCityFilter(city)} style={[styles.chip, cityFilter === city && styles.chipActive]}>
                  <Text style={[styles.chipText, cityFilter === city && styles.chipTextActive]}>{city}</Text>
                </Pressable>
              ) : null)}
            </ScrollView>
          </View>
        }
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Ionicons name="home-outline" size={42} color="#94a3b8" />
            <Text style={styles.emptyTitle}>עדיין אין התאמות</Text>
            <Text style={styles.empty}>התחל סריקה כדי שהסוכן ימצא דירות לפי ההעדפות שלך.</Text>
          </View>
        }
        contentContainerStyle={styles.listContent}
      />
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8fafc' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  offlineBanner: { backgroundColor: '#fef3c7', padding: 10 },
  offlineText: { textAlign: 'center', color: '#92400e', fontSize: 12, fontWeight: '600' },
  listContent: { paddingBottom: 28 },
  listHeader: { padding: 16, paddingBottom: 8 },
  welcome: { flexDirection: 'row-reverse', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  welcomeOverline: { fontSize: 13, color: '#64748b', textAlign: 'right' },
  welcomeTitle: { fontSize: 28, fontWeight: '800', color: '#0f172a', textAlign: 'right', marginTop: 2 },
  avatar: { width: 44, height: 44, borderRadius: 22, backgroundColor: '#ccfbf1', alignItems: 'center', justifyContent: 'center' },
  avatarText: { color: '#0f766e', fontSize: 18, fontWeight: '800' },
  scanCard: { backgroundColor: '#0f766e', borderRadius: 20, padding: 18, shadowColor: '#0f766e', shadowOpacity: 0.22, shadowRadius: 12, elevation: 4 },
  scanHeader: { flexDirection: 'row-reverse', justifyContent: 'space-between', alignItems: 'flex-start' },
  scanEyebrow: { color: '#99f6e4', fontSize: 12, fontWeight: '700' },
  scanTitle: { color: '#fff', fontSize: 19, fontWeight: '800', marginTop: 3 },
  statusDot: { width: 10, height: 10, borderRadius: 5, backgroundColor: '#5eead4', marginTop: 4 },
  statusDotActive: { backgroundColor: '#fbbf24' },
  scanDescription: { color: '#ccfbf1', fontSize: 13, lineHeight: 20, textAlign: 'right', marginTop: 12 },
  progressSection: { marginTop: 14 },
  progressTrack: { height: 7, backgroundColor: 'rgba(255,255,255,0.2)', borderRadius: 8, overflow: 'hidden' },
  progressValue: { height: '100%', backgroundColor: '#5eead4', borderRadius: 8 },
  progressText: { color: '#ecfeff', textAlign: 'right', fontSize: 13, marginTop: 8 },
  resultText: { color: '#99f6e4', textAlign: 'right', fontSize: 12, marginTop: 4, fontWeight: '700' },
  scanActions: { flexDirection: 'row-reverse', gap: 10, marginTop: 16 },
  scanButton: { flex: 1, flexDirection: 'row-reverse', gap: 8, backgroundColor: '#fff', borderRadius: 12, paddingVertical: 12, justifyContent: 'center', alignItems: 'center' },
  scanButtonDisabled: { opacity: 0.8 },
  scanButtonText: { color: '#0f766e', fontSize: 14, fontWeight: '800' },
  reportButton: { width: 46, borderRadius: 12, borderWidth: 1, borderColor: 'rgba(255,255,255,0.25)', alignItems: 'center', justifyContent: 'center' },
  metrics: { flexDirection: 'row-reverse', justifyContent: 'space-around', backgroundColor: '#fff', borderRadius: 16, paddingVertical: 13, marginTop: 12, borderWidth: 1, borderColor: '#e2e8f0' },
  metric: { alignItems: 'center', flex: 1 },
  metricValue: { color: '#0f172a', fontWeight: '800', fontSize: 14 },
  metricLabel: { color: '#64748b', fontSize: 10, marginTop: 3 },
  metricDivider: { width: 1, backgroundColor: '#e2e8f0' },
  sectionHeader: { flexDirection: 'row-reverse', justifyContent: 'space-between', alignItems: 'center', marginTop: 22, marginBottom: 10 },
  sectionTitle: { color: '#0f172a', fontSize: 18, fontWeight: '800' },
  sectionCount: { color: '#64748b', fontSize: 12 },
  segmented: { flexDirection: 'row-reverse', backgroundColor: '#e2e8f0', borderRadius: 11, padding: 3, marginBottom: 10 },
  segment: { flex: 1, paddingVertical: 8, borderRadius: 8, alignItems: 'center' },
  segmentActive: { backgroundColor: '#fff', shadowColor: '#0f172a', shadowOpacity: 0.08, shadowRadius: 3, elevation: 1 },
  segmentText: { color: '#64748b', fontWeight: '700', fontSize: 12 },
  segmentTextActive: { color: '#0f766e' },
  chips: { gap: 8, paddingVertical: 3, paddingHorizontal: 1, flexDirection: 'row-reverse' },
  chip: { borderWidth: 1, borderColor: '#e2e8f0', borderRadius: 20, paddingVertical: 7, paddingHorizontal: 12, backgroundColor: '#fff' },
  chipActive: { borderColor: '#0d9488', backgroundColor: '#f0fdfa' },
  chipText: { color: '#475569', fontSize: 12, fontWeight: '700' },
  chipTextActive: { color: '#0f766e' },
  propertyCard: {
    backgroundColor: '#fff',
    marginHorizontal: 12,
    marginVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    overflow: 'hidden',
  },
  propertyMain: { flexDirection: 'row-reverse', alignItems: 'center', padding: 14, gap: 12 },
  scoreWrap: { width: 46, height: 46, borderRadius: 23, borderWidth: 4, borderColor: '#99f6e4', alignItems: 'center', justifyContent: 'center' },
  score: { color: '#0f766e', fontWeight: '800', fontSize: 14, lineHeight: 16 },
  scoreLabel: { color: '#64748b', fontWeight: '700', fontSize: 8 },
  propertyContent: { flex: 1 },
  row: { flexDirection: 'row-reverse', justifyContent: 'space-between', marginBottom: 4 },
  city: { fontSize: 16, fontWeight: '700', color: '#0f172a' },
  price: { fontSize: 15, fontWeight: '700', color: '#0d9488' },
  meta: { fontSize: 13, color: '#64748b', textAlign: 'right' },
  valueLabel: { color: '#0f766e', fontSize: 11, fontWeight: '700', textAlign: 'right', marginTop: 5 },
  propertyDetails: { borderTopWidth: 1, borderTopColor: '#f1f5f9', padding: 14, gap: 10 },
  summary: { fontSize: 13, lineHeight: 20, color: '#334155', textAlign: 'right' },
  mortgageRow: { flexDirection: 'row-reverse', alignItems: 'center', gap: 6, backgroundColor: '#f0fdfa', borderRadius: 9, padding: 9 },
  mortgageText: { color: '#115e59', fontSize: 12, fontWeight: '700' },
  marketText: { color: '#64748b', fontSize: 12, lineHeight: 18, textAlign: 'right' },
  listingButton: { flexDirection: 'row-reverse', justifyContent: 'center', alignItems: 'center', gap: 6, backgroundColor: '#0d9488', borderRadius: 10, paddingVertical: 10 },
  listingButtonText: { color: '#fff', fontSize: 13, fontWeight: '800' },
  emptyState: { alignItems: 'center', padding: 40, gap: 10 },
  emptyTitle: { color: '#0f172a', fontSize: 17, fontWeight: '800' },
  empty: { textAlign: 'center', color: '#64748b', fontSize: 14, lineHeight: 22 },
})
