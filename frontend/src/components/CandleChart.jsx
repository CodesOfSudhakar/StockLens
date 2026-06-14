import { useEffect, useRef } from 'react'
import { createChart, CrosshairMode } from 'lightweight-charts'
import { useResolvedTheme } from '../store/useTheme.js'

// EMA line colours keyed by period (vivid on both light & dark).
const EMA_COLORS = {
  9: '#F59E0B',
  26: '#4F46E5',
  50: '#0EA5E9',
  100: '#9333EA',
}

function axisColors(theme) {
  return theme === 'dark'
    ? { text: '#B2B5C9', grid: 'rgba(255,255,255,0.06)', border: 'rgba(255,255,255,0.12)' }
    : { text: '#6B6F86', grid: 'rgba(26,26,46,0.05)', border: 'rgba(26,26,46,0.10)' }
}

function ema(values, period) {
  if (!values.length) return []
  const k = 2 / (period + 1)
  const out = []
  let prev = values[0].close
  for (const c of values) {
    prev = c.close * k + prev * (1 - k)
    out.push({ time: c.time, value: prev })
  }
  return out
}

export default function CandleChart({ candles = [], emaPeriods = [9, 26, 50, 100] }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)
  const theme = useResolvedTheme()

  useEffect(() => {
    if (!containerRef.current) return
    const c = axisColors(theme)
    const chart = createChart(containerRef.current, {
      height: 320,
      layout: {
        background: { color: 'transparent' },
        textColor: c.text,
        fontFamily: 'Plus Jakarta Sans, sans-serif',
        fontSize: 10,
      },
      grid: {
        vertLines: { color: c.grid },
        horzLines: { color: c.grid },
      },
      rightPriceScale: { borderColor: c.border },
      timeScale: { borderColor: c.border, timeVisible: true },
      crosshair: { mode: CrosshairMode.Normal },
      handleScale: { axisPressedMouseMove: true },
    })
    chartRef.current = chart

    const series = chart.addCandlestickSeries({
      upColor: '#10B981',
      downColor: '#F43F5E',
      borderUpColor: '#10B981',
      borderDownColor: '#F43F5E',
      wickUpColor: '#10B981',
      wickDownColor: '#F43F5E',
    })
    series.setData(candles)

    emaPeriods.forEach((p) => {
      const line = chart.addLineSeries({
        color: EMA_COLORS[p] || '#888',
        lineWidth: 1.5,
        priceLineVisible: false,
        lastValueVisible: false,
      })
      line.setData(ema(candles, p))
    })

    chart.timeScale().fitContent()

    const ro = new ResizeObserver((entries) => {
      const w = entries[0].contentRect.width
      chart.applyOptions({ width: w })
    })
    ro.observe(containerRef.current)

    return () => {
      ro.disconnect()
      chart.remove()
    }
  }, [candles, emaPeriods, theme])

  return (
    <div>
      <div ref={containerRef} className="w-full" />
      <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1">
        {emaPeriods.map((p) => (
          <span key={p} className="flex items-center gap-1 text-[10px] font-semibold text-muted">
            <span
              className="h-2 w-2 rounded-full"
              style={{ background: EMA_COLORS[p] || '#888' }}
            />
            EMA {p}
          </span>
        ))}
      </div>
    </div>
  )
}
