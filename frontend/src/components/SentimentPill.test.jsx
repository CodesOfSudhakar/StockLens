import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import SentimentPill from './SentimentPill.jsx'

describe('SentimentPill', () => {
  it('renders the value text by default', () => {
    render(<SentimentPill value="bullish" />)
    expect(screen.getByText('bullish')).toBeInTheDocument()
  })

  it('prefers an explicit label over the value', () => {
    render(<SentimentPill value="bullish" label="Risk-on" />)
    expect(screen.getByText('Risk-on')).toBeInTheDocument()
  })

  it('applies bearish styling for bearish/negative', () => {
    const { container } = render(<SentimentPill value="bearish" />)
    expect(container.querySelector('span').className).toContain('text-bearish')
  })

  it('is case-insensitive', () => {
    const { container } = render(<SentimentPill value="POSITIVE" />)
    expect(container.querySelector('span').className).toContain('text-bullish')
  })

  it('falls back to neutral for unknown values', () => {
    const { container } = render(<SentimentPill value="whatever" />)
    expect(container.querySelector('span').className).toContain('text-[#B45309]')
  })
})
