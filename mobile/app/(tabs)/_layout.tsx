import { Tabs } from 'expo-router'

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: '#0d9488',
        tabBarInactiveTintColor: '#64748b',
        headerTitleAlign: 'center',
      }}
    >
      <Tabs.Screen name="deals" options={{ title: 'דירות', tabBarLabel: 'דירות' }} />
      <Tabs.Screen name="alerts" options={{ title: 'התראות', tabBarLabel: 'התראות' }} />
      <Tabs.Screen name="map" options={{ title: 'מפה', tabBarLabel: 'מפה' }} />
      <Tabs.Screen name="camera" options={{ title: 'מצלמה', tabBarLabel: 'מצלמה' }} />
      <Tabs.Screen name="settings" options={{ title: 'הגדרות', tabBarLabel: 'הגדרות' }} />
    </Tabs>
  )
}
