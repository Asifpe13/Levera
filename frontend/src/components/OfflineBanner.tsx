import { useEffect, useState } from 'react'
import { isOnline } from '../services/propertyCache'

export default function OfflineBanner() {
  const [online, setOnline] = useState(isOnline())
  const [showStaleHint, setShowStaleHint] = useState(false)

  useEffect(() => {
    function onOnline() {
      setOnline(true)
      setShowStaleHint(false)
    }
    function onOffline() {
      setOnline(false)
      setShowStaleHint(true)
    }
    window.addEventListener('online', onOnline)
    window.addEventListener('offline', onOffline)
    return () => {
      window.removeEventListener('online', onOnline)
      window.removeEventListener('offline', onOffline)
    }
  }, [])

  if (online && !showStaleHint) return null

  return (
    <div
      className={`fixed top-0 inset-x-0 z-[60] px-4 py-2 text-center text-xs font-semibold safe-top ${
        online ? 'bg-amber-500 text-white' : 'bg-slate-800 text-white'
      }`}
      role="status"
    >
      {online
        ? 'חזר חיבור — מרענן נתונים...'
        : 'אין חיבור — מציג דירות שמורות מהזיכרון המקומי'}
    </div>
  )
}
