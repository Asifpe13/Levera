import { useState } from 'react'
import { Pressable, StyleSheet, Switch, Text, View } from 'react-native'
import { router } from 'expo-router'

import { updateUser } from '@/src/api'
import { useAuth } from '@/src/auth'

export default function SettingsScreen() {
  const { user, logout, refreshUser } = useAuth()
  const [pushEnabled, setPushEnabled] = useState(user?.push_notifications ?? true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  async function togglePush(value: boolean) {
    setPushEnabled(value)
    setSaving(true)
    try {
      await updateUser({ push_notifications: value })
      await refreshUser()
      setMessage('נשמר')
    } catch {
      setPushEnabled(!value)
      setMessage('שגיאה בשמירה')
    } finally {
      setSaving(false)
    }
  }

  if (!user) return null

  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.label}>שם</Text>
        <Text style={styles.value}>{user.name}</Text>
        <Text style={styles.label}>אימייל</Text>
        <Text style={styles.value}>{user.email}</Text>
        <Text style={styles.label}>ערים</Text>
        <Text style={styles.value}>{user.target_cities?.join(', ') || '—'}</Text>
      </View>

      <View style={styles.card}>
        <View style={styles.row}>
          <Switch
            value={pushEnabled}
            onValueChange={togglePush}
            disabled={saving}
            trackColor={{ true: '#99f6e4', false: '#cbd5e1' }}
            thumbColor={pushEnabled ? '#0d9488' : '#f1f5f9'}
          />
          <Text style={styles.switchLabel}>התראות Push</Text>
        </View>
        {message ? <Text style={styles.message}>{message}</Text> : null}
      </View>

      <Pressable
        style={styles.logout}
        onPress={async () => {
          await logout()
          router.replace('/login')
        }}
      >
        <Text style={styles.logoutText}>התנתק</Text>
      </Pressable>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8fafc', padding: 16, gap: 12 },
  card: {
    backgroundColor: '#fff',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    gap: 6,
  },
  label: { fontSize: 12, color: '#64748b', textAlign: 'right', marginTop: 8 },
  value: { fontSize: 16, color: '#0f172a', textAlign: 'right', fontWeight: '600' },
  row: { flexDirection: 'row-reverse', alignItems: 'center', justifyContent: 'space-between' },
  switchLabel: { fontSize: 16, fontWeight: '600', color: '#0f172a' },
  message: { fontSize: 12, color: '#0d9488', textAlign: 'right' },
  logout: {
    marginTop: 'auto',
    backgroundColor: '#f1f5f9',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  logoutText: { color: '#475569', fontWeight: '700', fontSize: 16 },
})
