import { useEffect } from 'react'
import { useAuth } from '../AuthContext'
import { registerDeviceToken, removeDeviceToken } from '../api'
import { getPlatform, isNativeApp } from '../utils/platform'

export default function PushNotificationsManager() {
  const { token, user } = useAuth()

  useEffect(() => {
    if (!token || !user) return

    let cancelled = false
    let registeredToken: string | null = null

    async function setupPush() {
      const platform = getPlatform()

      if (isNativeApp()) {
        try {
          const { PushNotifications } = await import('@capacitor/push-notifications')

          const perm = await PushNotifications.requestPermissions()
          if (perm.receive !== 'granted') return

          await PushNotifications.register()

          const regListener = await PushNotifications.addListener('registration', async (ev) => {
            if (cancelled || !ev.value) return
            registeredToken = ev.value
            await registerDeviceToken(ev.value, platform === 'ios' ? 'ios' : 'android')
          })

          const errListener = await PushNotifications.addListener('registrationError', (err) => {
            console.warn('Push registration error', err)
          })

          const actionListener = await PushNotifications.addListener(
            'pushNotificationActionPerformed',
            () => {
              window.location.href = '/app'
            },
          )

          return () => {
            regListener.remove()
            errListener.remove()
            actionListener.remove()
          }
        } catch (err) {
          console.warn('Capacitor push unavailable', err)
        }
        return
      }

      if ('serviceWorker' in navigator && 'PushManager' in window) {
        try {
          const reg = await navigator.serviceWorker.ready
          const existing = await reg.pushManager.getSubscription()
          if (existing?.endpoint) {
            registeredToken = existing.endpoint
            await registerDeviceToken(existing.endpoint, 'web')
          }
        } catch {
          // Web push requires VAPID keys — optional for local dev
        }
      }
    }

    const cleanupPromise = setupPush()

    return () => {
      cancelled = true
      if (registeredToken) {
        removeDeviceToken(registeredToken, getPlatform() === 'ios' ? 'ios' : 'web').catch(() => {})
      }
      cleanupPromise.then((cleanup) => cleanup?.())
    }
  }, [token, user])

  return null
}
