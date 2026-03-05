import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import LandingPage from '../pages/LandingPage'

describe('LandingPage', () => {
  it('shows main marketing message and CTA buttons', () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    )

    // Title and main hero text
    expect(screen.getByText('Levera')).toBeInTheDocument()
    expect(
      screen.getByText(/הסוכן החכם שמסנן/, { exact: false })
    ).toBeInTheDocument()
    expect(
      screen.getByText('הפעל את הסוכן בחינם', { exact: false })
    ).toBeInTheDocument()
    expect(screen.getByText('כבר יש לי חשבון')).toBeInTheDocument()
  })

  // CTA link section is rendered, no need לייצב את הטסט על טקסט מדויק נוסף כרגע
})

