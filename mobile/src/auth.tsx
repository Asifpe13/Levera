import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import * as Notifications from 'expo-notifications'
import * as Device from 'expo-device'
import { Platform } from 'react-native'
import { getUser, login as apiLogin, registerDeviceToken, setToken, type User } from './api'

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
})

interface AuthContextValue {
  user: User | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

async function registerForPush(userEmail: string) {
  if (!Device.isDevice) return

  const { status: existing } = await Notifications.getPermissionsAsync()
  let finalStatus = existing
  if (existing !== 'granted') {
    const req = await Notifications.requestPermissionsAsync()
    finalStatus = req.status
  }
  if (finalStatus !== 'granted') return

  const pushToken = (await Notifications.getExpoPushTokenAsync()).data
  if (pushToken) {
    await registerDeviceToken(pushToken)
  }

  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'Levera',
      importance: Notifications.AndroidImportance.MAX,
    })
  }

  console.log('[push] registered for', userEmail)
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setTokenState] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    const u = await getUser()
    setUser(u)
  }, [])

  useEffect(() => {
    ;(async () => {
      try {
        const { getToken } = await import('./api')
        const t = await getToken()
        if (t) {
          setTokenState(t)
          const u = await getUser()
          setUser(u)
          await registerForPush(u.email)
        }
      } catch {
        await setToken(null)
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const res = await apiLogin(email, password)
    if (!res.token) throw new Error('לא התקבל token')
    await setToken(res.token)
    setTokenState(res.token)
    const u = await getUser()
    setUser(u)
    await registerForPush(u.email)
  }, [])

  const logout = useCallback(async () => {
    await setToken(null)
    setTokenState(null)
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({ user, token, loading, login, logout, refreshUser }),
    [user, token, loading, login, logout, refreshUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth outside AuthProvider')
  return ctx
}
