import { useEffect, useState } from 'react'
import { isNativeApp, isStandalonePwa } from '../utils/platform'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

const DISMISS_KEY = 'levera_install_dismissed'

export default function InstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (isNativeApp() || isStandalonePwa()) return
    if (localStorage.getItem(DISMISS_KEY)) return

    function onBeforeInstall(e: Event) {
      e.preventDefault()
      setDeferredPrompt(e as BeforeInstallPromptEvent)
      setVisible(true)
    }

    window.addEventListener('beforeinstallprompt', onBeforeInstall)
    return () => window.removeEventListener('beforeinstallprompt', onBeforeInstall)
  }, [])

  async function handleInstall() {
    if (!deferredPrompt) return
    await deferredPrompt.prompt()
    const { outcome } = await deferredPrompt.userChoice
    if (outcome === 'accepted') setVisible(false)
    setDeferredPrompt(null)
  }

  function handleDismiss() {
    localStorage.setItem(DISMISS_KEY, '1')
    setVisible(false)
  }

  if (!visible) return null

  return (
    <div className="fixed bottom-20 md:bottom-6 left-3 right-3 md:left-auto md:right-6 md:max-w-sm z-50 safe-bottom">
      <div className="levera-card p-4 shadow-elevated border-teal-200/60 bg-white/95 backdrop-blur-sm">
        <div className="flex items-start gap-3">
          <img src="/icons/icon-72.png" alt="" className="w-12 h-12 rounded-xl flex-shrink-0" />
          <div className="min-w-0 flex-1">
            <p className="font-bold text-slate-800 text-sm">התקן את Levera</p>
            <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">
              הוסף את הסוכן למסך הבית לגישה מהירה מהטלפון
            </p>
          </div>
        </div>
        <div className="flex gap-2 mt-3">
          <button
            type="button"
            onClick={handleInstall}
            className="flex-1 py-2 px-3 rounded-lg bg-teal-600 text-white text-sm font-semibold hover:bg-teal-700 transition-colors"
          >
            התקן
          </button>
          <button
            type="button"
            onClick={handleDismiss}
            className="py-2 px-3 rounded-lg text-slate-600 text-sm font-medium hover:bg-slate-100 transition-colors"
          >
            לא עכשיו
          </button>
        </div>
      </div>
    </div>
  )
}
