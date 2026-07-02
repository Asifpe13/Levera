import { Redirect } from 'expo-router'
import { ActivityIndicator, View } from 'react-native'

import { useAuth } from '@/src/auth'

export default function Index() {
  const { token, loading } = useAuth()

  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#0d9488" />
      </View>
    )
  }

  if (token) return <Redirect href="/(tabs)/deals" />
  return <Redirect href="/login" />
}
