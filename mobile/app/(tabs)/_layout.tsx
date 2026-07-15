import { Tabs } from 'expo-router'
import { Ionicons } from '@expo/vector-icons'

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: '#0d9488',
        tabBarInactiveTintColor: '#64748b',
        headerTitleAlign: 'center',
        tabBarLabelStyle: { fontSize: 11, fontWeight: '700' },
        tabBarStyle: { height: 64, paddingTop: 5 },
      }}
    >
      <Tabs.Screen name="deals" options={{ title: 'דירות', tabBarLabel: 'דירות', tabBarIcon: ({ color, size }) => <Ionicons name="home-outline" color={color} size={size} /> }} />
      <Tabs.Screen name="alerts" options={{ title: 'התראות', tabBarLabel: 'התראות', tabBarIcon: ({ color, size }) => <Ionicons name="notifications-outline" color={color} size={size} /> }} />
      <Tabs.Screen name="map" options={{ title: 'מפה', tabBarLabel: 'מפה', tabBarIcon: ({ color, size }) => <Ionicons name="map-outline" color={color} size={size} /> }} />
      <Tabs.Screen name="camera" options={{ title: 'מצלמה', tabBarLabel: 'מצלמה', tabBarIcon: ({ color, size }) => <Ionicons name="camera-outline" color={color} size={size} /> }} />
      <Tabs.Screen name="settings" options={{ title: 'הגדרות', tabBarLabel: 'הגדרות', tabBarIcon: ({ color, size }) => <Ionicons name="settings-outline" color={color} size={size} /> }} />
    </Tabs>
  )
}
