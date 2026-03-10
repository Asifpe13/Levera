import { render, screen, fireEvent } from '@testing-library/react'
import PropertyCard from '../components/PropertyCard'
import type { Property } from '../api'

const BASE_PROP: Property = {
  id: 'p1',
  source: 'Yad2',
  source_id: '123',
  deal_type: 'sale',
  city: 'תל אביב - יפו',
  neighborhood: 'לב העיר',
  address: 'הרצל 10',
  rooms: 4,
  floor: 3,
  size_sqm: 90,
  price: 1_500_000,
  ai_score: 85,
  ai_summary: 'נכס מצוין להשקעה',
  listing_url: 'https://example.com/listing/123',
  monthly_repayment: 5_200,
  loan_amount: 1_200_000,
}

describe('PropertyCard', () => {
  it('renders city, rooms and price in header', () => {
    render(<PropertyCard prop={BASE_PROP} />)
    expect(screen.getByText(/תל אביב - יפו/)).toBeInTheDocument()
    expect(screen.getByText(/4 חד/)).toBeInTheDocument()
    expect(screen.getByText(/1,500,000/)).toBeInTheDocument()
  })

  it('shows score ring', () => {
    render(<PropertyCard prop={BASE_PROP} />)
    expect(screen.getByText('85')).toBeInTheDocument()
  })

  it('expands details on click when score >= 70', () => {
    render(<PropertyCard prop={BASE_PROP} />)
    // score=85 → starts expanded; details should already be visible
    expect(screen.getByText('הרצל 10')).toBeInTheDocument()
  })

  it('collapses details on click when already open', () => {
    render(<PropertyCard prop={BASE_PROP} />)
    const header = screen.getByRole('button')
    fireEvent.click(header)  // collapse
    expect(screen.queryByText('הרצל 10')).not.toBeInTheDocument()
    fireEvent.click(header)  // expand again
    expect(screen.getByText('הרצל 10')).toBeInTheDocument()
  })

  it('shows AI summary when expanded', () => {
    render(<PropertyCard prop={BASE_PROP} />)
    expect(screen.getByText('נכס מצוין להשקעה')).toBeInTheDocument()
  })

  it('shows mortgage details for sale properties', () => {
    render(<PropertyCard prop={BASE_PROP} />)
    expect(screen.getByText(/5,200/)).toBeInTheDocument()
    expect(screen.getByText(/1,200,000/)).toBeInTheDocument()
  })

  it('renders listing link', () => {
    render(<PropertyCard prop={BASE_PROP} />)
    const links = screen.getAllByRole('link')
    expect(links.some((l) => l.getAttribute('href') === BASE_PROP.listing_url)).toBe(true)
  })

  it('shows market comparison block when market data present', () => {
    const prop: Property = {
      ...BASE_PROP,
      market_summary_text: 'דירות דומות נמכרו ב-₪20,000 למ"ר',
    }
    render(<PropertyCard prop={prop} />)
    expect(screen.getByText(/דירות דומות/)).toBeInTheDocument()
  })

  it('shows profile area message when present', () => {
    const prop: Property = {
      ...BASE_PROP,
      profile_area_message: 'באזור זה דירות נמכרו בממוצע ב-₪18,000 למ"ר',
    }
    render(<PropertyCard prop={prop} />)
    expect(screen.getByText(/₪18,000/)).toBeInTheDocument()
  })

  it('does not show mortgage block for rent properties', () => {
    const prop: Property = {
      ...BASE_PROP,
      deal_type: 'rent',
      price: 6_000,
      monthly_repayment: undefined,
      loan_amount: undefined,
    }
    render(<PropertyCard prop={prop} />)
    expect(screen.queryByText(/משכנתא לפי חוק/)).not.toBeInTheDocument()
  })

  it('shows market confidence badge when available', () => {
    const prop: Property = { ...BASE_PROP, market_confidence: 75 }
    render(<PropertyCard prop={prop} />)
    expect(screen.getByText(/ביטחון שוק 75/)).toBeInTheDocument()
  })

  it('starts collapsed when score < 70', () => {
    const prop: Property = { ...BASE_PROP, ai_score: 45 }
    render(<PropertyCard prop={prop} />)
    expect(screen.queryByText('הרצל 10')).not.toBeInTheDocument()
  })
})
