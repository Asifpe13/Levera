import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react'
import { getUser, type User } from './api'

const tokenKey = 'aigent_token'

type AuthContextType = {
  user: User | null
  token: string | null
  setToken: (t: string | null) => void
  setUser: (u: User | null) => void
  loadUser: () => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setTokenState] = useState<string | null>(() => localStorage.getItem(tokenKey))

  const setToken = useCallback((t: string | null) => {
    if (t) localStorage.setItem(tokenKey, t)
    else localStorage.removeItem(tokenKey)
    setTokenState(t)
  }, [])

  const loadUser = useCallback(async () => {
    if (!token) {
      setUser(null)
      return
    }
    try {
      const u = await getUser()
      setUser(u)
    } catch {
      setToken(null)
      setUser(null)
    }
  }, [token, setToken])

  useEffect(() => {
    loadUser()
  }, [loadUser])

  const logout = useCallback(() => {
    setToken(null)
    setUser(null)
  }, [setToken])

  return (
    <AuthContext.Provider value={{ user, token, setToken, setUser, loadUser, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
