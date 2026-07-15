import { useState } from 'react'
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native'
import { router } from 'expo-router'

import { useAuth } from '@/src/auth'

export default function RegisterScreen() {
  const { register } = useAuth()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [city, setCity] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleRegister() {
    const cleanCity = city.trim()
    if (!name.trim() || !email.trim() || !password || !cleanCity) {
      setError('יש למלא שם, אימייל, סיסמה ועיר לחיפוש')
      return
    }

    setError('')
    setLoading(true)
    try {
      await register({
        name: name.trim(),
        email: email.trim(),
        password,
        target_cities: [cleanCity],
      })
      router.replace('/(tabs)/deals')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'לא ניתן היה ליצור חשבון')
    } finally {
      setLoading(false)
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        <View style={styles.card}>
          <Text style={styles.title}>יצירת חשבון</Text>
          <Text style={styles.subtitle}>מתחילים עם אזור החיפוש הראשון שלך</Text>

          <TextInput
            style={styles.input}
            placeholder="שם מלא"
            value={name}
            onChangeText={setName}
            textAlign="right"
            autoComplete="name"
          />
          <TextInput
            style={styles.input}
            placeholder="אימייל"
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            keyboardType="email-address"
            textAlign="right"
            autoComplete="email"
          />
          <TextInput
            style={styles.input}
            placeholder="סיסמה (6 תווים לפחות)"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            textAlign="right"
            autoComplete="new-password"
          />
          <TextInput
            style={styles.input}
            placeholder="עיר לחיפוש, למשל תל אביב - יפו"
            value={city}
            onChangeText={setCity}
            textAlign="right"
          />

          {error ? <Text style={styles.error}>{error}</Text> : null}

          <Pressable style={styles.button} onPress={handleRegister} disabled={loading}>
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>צור חשבון</Text>
            )}
          </Pressable>

          <Pressable
            style={styles.secondaryButton}
            onPress={() => router.replace('/login')}
            disabled={loading}
          >
            <Text style={styles.secondaryButtonText}>כבר יש לך חשבון? להתחברות</Text>
          </Pressable>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8fafc' },
  scroll: { flexGrow: 1, justifyContent: 'center', padding: 20 },
  card: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 24,
    gap: 12,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  title: { fontSize: 26, fontWeight: '800', color: '#0f766e', textAlign: 'center' },
  subtitle: { fontSize: 14, color: '#64748b', textAlign: 'center', marginBottom: 8 },
  input: {
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 12,
    padding: 14,
    fontSize: 16,
    backgroundColor: '#fff',
  },
  button: {
    backgroundColor: '#0d9488',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonText: { color: '#fff', fontWeight: '700', fontSize: 16 },
  secondaryButton: { alignItems: 'center', padding: 10 },
  secondaryButtonText: { color: '#0f766e', fontWeight: '700', fontSize: 14 },
  error: { color: '#dc2626', textAlign: 'center', fontSize: 13 },
})
