import { useEffect, useRef } from 'react'
import { createChart, LineStyle } from 'lightweight-charts'
import { useResolvedTheme } from '../store/useTheme.js'

export default function RSIPanel({ rsi = [] }) {
  const ref = useRef(null)
  const theme = useResolvedTheme()
  const last = rsi.length ? rsi[rsi.length - 1].value : null

  useEffect(() => {
    if (!ref.current) return
    const text = theme === 'dark' ? '#B2B5C9' : '#6B6F86'
    const border = theme === 'dark' ? 'rgba(255,255,255,0.12)' : 'rgba(26,26,46,0.10)'
    const chart = createChart(ref.current, {
      height: 120,
      layout: {
        background: { color: 'transparent' },
        textColor: text,
        fontFamily: 'Plus Jakarta Sans, sans-serif',
        fontSize: 10,
      },
      grid: { vertLines: { visible: false }, horzLines: { visible: false } },
      rightPriceScale: { borderColor: border },
      timeScale: { visible: false, borderVisible: false },
      handleScale: false,
      handleScroll: false,
    })

    const line = chart.addLineSeries({ color: '#4F46E5', lineWidth: 2 })
    line.setData(rsi)
    line.createPriceLine({ price: 70, color: '#F43F5E', lineWidth: 1, lineStyle: LineStyle.Dashed, axisLabelVisible: true, title: '70' })
    line.createPriceLine({ price: 30, color: '#10B981', lineWidth: 1, lineStyle: LineStyle.Dashed, axisLabelVisible: true, title: '30' })
    chart.timeScale().fitContent()

    const ro = new ResizeObserver((e) => chart.applyOptions({ width: e[0].contentRect.width }))
    ro.observe(ref.current)
    return () => {
      ro.disconnect()
      chart.remove()
    }
  }, [rsi, theme])

  const zone =
    last == null ? '' : last >= 70 ? 'Overbought' : last <= 30 ? 'Oversold' : 'Neutral'
  const zoneColor = last >= 70 ? 'text-bearish' : last <= 30 ? 'text-bullish' : 'text-neutral'

  return (
    <div className="card p-4">
      <div className="mb-1 flex items-center justify-between">
        <h3 className="text-sm font-bold text-primary">RSI (14)</h3>
        {last != null && (
          <span className={`text-sm font-bold ${zoneColor}`}>
            {last.toFixed(1)} · {zone}
          </span>
        )}
      </div>
      <div ref={ref} className="w-full" />
    </div>
  )
}
