/** Platform detection for web, PWA, and Capacitor native shells */

export type AppPlatform = 'web' | 'pwa' | 'ios' | 'android'

export function isNativeApp(): boolean {
  return typeof window !== 'undefined' && !!(window as Window & { Capacitor?: { isNativePlatform?: () => boolean } }).Capacitor?.isNativePlatform?.()
}

export function isStandalonePwa(): boolean {
  if (typeof window === 'undefined') return false
  const standalone =
    typeof window.matchMedia === 'function' &&
    window.matchMedia('(display-mode: standalone)').matches
  return (
    standalone ||
    (window.navigator as Navigator & { standalone?: boolean }).standalone === true
  )
}

export function getPlatform(): AppPlatform {
  if (typeof window === 'undefined') return 'web'
  const cap = (window as Window & { Capacitor?: { getPlatform?: () => string } }).Capacitor
  const nativePlatform = cap?.getPlatform?.()
  if (nativePlatform === 'ios') return 'ios'
  if (nativePlatform === 'android') return 'android'
  if (isStandalonePwa()) return 'pwa'
  return 'web'
}

export function isMobileViewport(): boolean {
  if (typeof window === 'undefined') return false
  if (typeof window.matchMedia !== 'function') return false
  return window.matchMedia('(max-width: 767px)').matches
}
