import { useEffect } from 'react'
import { isNativeApp } from '../utils/platform'

export default function NativeShell() {
  useEffect(() => {
    if (!isNativeApp()) return

    async function initNative() {
      try {
        const { StatusBar, Style } = await import('@capacitor/status-bar')
        const { SplashScreen } = await import('@capacitor/splash-screen')
        const { App } = await import('@capacitor/app')

        await StatusBar.setStyle({ style: Style.Light })
        await StatusBar.setBackgroundColor({ color: '#0d9488' })
        await SplashScreen.hide()

        App.addListener('backButton', ({ canGoBack }) => {
          if (canGoBack) {
            window.history.back()
          } else {
            App.exitApp()
          }
        })
      } catch {
        // Capacitor plugins unavailable in web build
      }
    }

    initNative()
  }, [])

  return null
}
