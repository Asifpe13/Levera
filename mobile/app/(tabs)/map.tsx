import { useEffect, useState } from 'react'
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native'
import MapView, { Marker } from 'react-native-maps'
import * as Location from 'expo-location'

import { getProperties, type Property } from '@/src/api'

const ISRAEL_REGION = {
  latitude: 31.7683,
  longitude: 35.2137,
  latitudeDelta: 0.8,
  longitudeDelta: 0.8,
}

/** Rough city coordinates for demo markers when property has no lat/lng */
const CITY_COORDS: Record<string, { lat: number; lng: number }> = {
  'תל אביב - יפו': { lat: 32.0853, lng: 34.7818 },
  'פתח תקווה': { lat: 32.084, lng: 34.8878 },
  'ירושלים': { lat: 31.7683, lng: 35.2137 },
  'חיפה': { lat: 32.794, lng: 34.9896 },
  'ראשון לציון': { lat: 31.973, lng: 34.7925 },
}

function markerForProperty(p: Property, index: number) {
  const city = p.city?.trim()
  const base = (city && CITY_COORDS[city]) || ISRAEL_REGION
  const jitter = (index % 7) * 0.008
  return {
    latitude: base.lat + jitter,
    longitude: base.lng + jitter,
    title: city,
    description: `₪${p.price?.toLocaleString('he-IL')}`,
  }
}

export default function MapScreen() {
  const [properties, setProperties] = useState<Property[]>([])
  const [loading, setLoading] = useState(true)
  const [location, setLocation] = useState<{ latitude: number; longitude: number } | null>(null)

  useEffect(() => {
    ;(async () => {
      try {
        const { status } = await Location.requestForegroundPermissionsAsync()
        if (status === 'granted') {
          const loc = await Location.getCurrentPositionAsync({})
          setLocation({
            latitude: loc.coords.latitude,
            longitude: loc.coords.longitude,
          })
        }
      } catch {
        // Location optional
      }

      try {
        setProperties(await getProperties({ view: 'all', limit: 30 }))
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#0d9488" />
      </View>
    )
  }

  return (
    <View style={styles.container}>
      <MapView
        style={styles.map}
        initialRegion={ISRAEL_REGION}
        showsUserLocation={!!location}
      >
        {location && (
          <Marker coordinate={location} title="המיקום שלך" pinColor="#6366f1" />
        )}
        {properties.map((p, i) => {
          const m = markerForProperty(p, i)
          return <Marker key={p.id || String(i)} coordinate={m} title={m.title} description={m.description} />
        })}
      </MapView>
      <View style={styles.legend}>
        <Text style={styles.legendText}>{properties.length} דירות על המפה (לפי עיר)</Text>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  map: { flex: 1 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  legend: {
    position: 'absolute',
    bottom: 16,
    alignSelf: 'center',
    backgroundColor: 'rgba(255,255,255,0.95)',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
  },
  legendText: { fontSize: 12, fontWeight: '600', color: '#0f766e' },
})
