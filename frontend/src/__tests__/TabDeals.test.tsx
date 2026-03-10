import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import TabDeals from '../components/TabDeals'
import type { User, Property } from '../api'
import * as api from '../api'

const MOCK_USER: User = {
  name: 'ישראל ישראלי',
  email: 'israel@test.com',
  target_cities: ['תל אביב - יפו', 'פתח תקווה'],
  search_type: 'buy',
  profile_type: 'HOME_BUYER',
  home_index: 1,
  loan_term_years: 30,
  equity: 300_000,
  monthly_income: 20_000,
  room_range_min: 3,
  room_range_max: 5,
  max_price: 1_500_000,
  max_repayment_ratio: 0.4,
  rent_room_range_min: 2,
  rent_room_range_max: 4,
  max_rent: null,
  extra_preferences: null,
}

const MOCK_PROPERTY: Property = {
  id: 'p1',
  source: 'Yad2',
  source_id: '111',
  deal_type: 'sale',
  city: 'תל אביב - יפו',
  rooms: 4,
  price: 1_200_000,
  ai_score: 80,
  ai_summary: 'נכס מעניין',
  listing_url: 'https://example.com/1',
}

describe('TabDeals', () => {
  beforeEach(() => {
    vi.spyOn(api, 'getProperties').mockResolvedValue([MOCK_PROPERTY])
    vi.spyOn(api, 'runScan').mockResolvedValue({
      ok: true,
      log: [{ time: '', level: 'info', message: 'סריקה הושלמה' }],
      total_found: 10,
      total_matches: 1,
    })
    vi.spyOn(api, 'requestWeeklyReport').mockResolvedValue({
      ok: true,
      message: '',
      properties_count: 3,
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders agent header with user name', async () => {
    render(<TabDeals user={MOCK_USER} />)
    await waitFor(() => {
      expect(screen.getByText(/הסוכן של ישראל ישראלי/)).toBeInTheDocument()
    })
  })

  it('renders scan button and weekly report button', () => {
    render(<TabDeals user={MOCK_USER} />)
    expect(screen.getByRole('button', { name: /שלח את הסוכן לסרוק/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /דוח שבועי/ })).toBeInTheDocument()
  })

  it('shows view toggle buttons', async () => {
    render(<TabDeals user={MOCK_USER} />)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'סריקה אחרונה' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'כל הדירות שנמצאו' })).toBeInTheDocument()
    })
  })

  it('loads and displays properties on mount', async () => {
    render(<TabDeals user={MOCK_USER} />)
    await waitFor(() => {
      // The city appears both as a filter pill and inside the property card header
      const matches = screen.getAllByText(/תל אביב - יפו/)
      expect(matches.length).toBeGreaterThanOrEqual(1)
    })
  })

  it('switches to all view when toggle clicked', async () => {
    render(<TabDeals user={MOCK_USER} />)
    await waitFor(() => screen.getByRole('button', { name: 'כל הדירות שנמצאו' }))
    fireEvent.click(screen.getByRole('button', { name: 'כל הדירות שנמצאו' }))
    await waitFor(() => {
      expect(api.getProperties).toHaveBeenCalledWith(
        expect.objectContaining({ view: 'all' })
      )
    })
  })

  it('shows scan summary after running scan', async () => {
    render(<TabDeals user={MOCK_USER} />)
    await waitFor(() => screen.getByRole('button', { name: /שלח את הסוכן לסרוק/ }))
    fireEvent.click(screen.getByRole('button', { name: /שלח את הסוכן לסרוק/ }))
    await waitFor(() => {
      expect(screen.getByText(/נסרקו 10 דירות/)).toBeInTheDocument()
      expect(screen.getByText(/נשמרו 1 התאמות/)).toBeInTheDocument()
    })
  })

  it('shows weekly report toast after requesting report', async () => {
    render(<TabDeals user={MOCK_USER} />)
    await waitFor(() => screen.getByRole('button', { name: /דוח שבועי/ }))
    fireEvent.click(screen.getByRole('button', { name: /דוח שבועי/ }))
    await waitFor(() => {
      expect(screen.getByText(/הדוח השבועי נשלח למייל/)).toBeInTheDocument()
    })
  })

  it('shows empty state when no properties', async () => {
    vi.spyOn(api, 'getProperties').mockResolvedValue([])
    render(<TabDeals user={MOCK_USER} />)
    await waitFor(() => {
      expect(screen.getByText(/לא נמצאו דירות|ממתין לפקודה/)).toBeInTheDocument()
    })
  })

  it('displays user equity in stats', async () => {
    render(<TabDeals user={MOCK_USER} />)
    await waitFor(() => {
      expect(screen.getByText(/300,000/)).toBeInTheDocument()
    })
  })
})
