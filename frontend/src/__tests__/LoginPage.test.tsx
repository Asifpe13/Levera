import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import LoginPage from '../pages/LoginPage'
import { AuthProvider } from '../AuthContext'
import * as api from '../api'

function renderLogin() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    </MemoryRouter>
  )
}

describe('LoginPage', () => {
  it('renders the login form', () => {
    renderLogin()
    expect(screen.getByText('כניסה לחשבון האישי')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('your@email.com')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /כניסה ל.Levera/i })).toBeInTheDocument()
  })

  it('shows error when submitting empty email', async () => {
    renderLogin()
    fireEvent.click(screen.getByRole('button', { name: /כניסה ל.Levera/i }))
    await waitFor(() => {
      expect(screen.getByText('יש להזין כתובת אימייל')).toBeInTheDocument()
    })
  })

  it('shows error message from API on failed login', async () => {
    vi.spyOn(api, 'login').mockRejectedValueOnce(new Error('לא נמצא חשבון'))
    renderLogin()
    fireEvent.change(screen.getByPlaceholderText('your@email.com'), {
      target: { value: 'notfound@test.com' },
    })
    fireEvent.click(screen.getByRole('button', { name: /כניסה ל.Levera/i }))
    await waitFor(() => {
      expect(screen.getByText(/לא נמצא חשבון/)).toBeInTheDocument()
    })
  })

  it('renders back-to-home button', () => {
    renderLogin()
    expect(screen.getByText(/חזרה לעמוד הראשי/)).toBeInTheDocument()
  })

  it('renders link to register page', () => {
    renderLogin()
    expect(screen.getByText('יצירת חשבון חדש')).toBeInTheDocument()
  })
})
