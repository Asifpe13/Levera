import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from '../App'

describe('App routing', () => {
  it('renders landing page hero on root route', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    )

    expect(
      screen.getByText(/הסוכן החכם שמסנן/, { exact: false })
    ).toBeInTheDocument()
  })

  it('redirects unauthenticated /app to login', () => {
    render(
      <MemoryRouter initialEntries={['/app']}>
        <App />
      </MemoryRouter>
    )

    expect(screen.getByText('כניסה לחשבון האישי')).toBeInTheDocument()
  })
})

