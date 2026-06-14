import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import IndexCard from './IndexCard.jsx'

const base = { symbol: 'NIFTY', label: 'Nifty 50', ltp: 24715.22, changePct: -0.34 }

describe('IndexCard', () => {
  it('renders label and formatted price', () => {
    render(<IndexCard index={{ ...base, change: -84.78 }} />)
    expect(screen.getByText('Nifty 50')).toBeInTheDocument()
    expect(screen.getByText('24,715.22')).toBeInTheDocument()
  })

  it('shows a down arrow and bearish colour on a fall', () => {
    const { container } = render(<IndexCard index={{ ...base, change: -84.78 }} />)
    expect(container.textContent).toContain('▼')
    expect(container.querySelector('.text-bearish')).toBeTruthy()
  })

  it('shows an up arrow and bullish colour on a rise', () => {
    const { container } = render(
      <IndexCard index={{ symbol: 'BANKNIFTY', label: 'Bank Nifty', ltp: 53047.31, change: 647.31, changePct: 1.24 }} />
    )
    expect(container.textContent).toContain('▲')
    expect(container.querySelector('.text-bullish')).toBeTruthy()
  })

  it('fires onClick when tapped', () => {
    const onClick = vi.fn()
    render(<IndexCard index={{ ...base, change: 1 }} onClick={onClick} />)
    fireEvent.click(screen.getByRole('button'))
    expect(onClick).toHaveBeenCalledOnce()
  })
})
