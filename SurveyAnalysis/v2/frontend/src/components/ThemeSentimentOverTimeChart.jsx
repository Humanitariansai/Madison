import { useState } from 'react'

/**
 * X-Y chart: time (period) on X-axis, count on Y-axis.
 * Shows count labels on the graph; click a period to see sample comments.
 */
const ThemeSentimentOverTimeChart = ({ themeName, data, frequency = 'D' }) => {
  const [selectedIndex, setSelectedIndex] = useState(null)

  if (!data || data.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
        <p className="text-gray-400 text-sm">No time-based data for this theme. A date/time column may be missing in your data.</p>
      </div>
    )
  }

  const sortedData = [...data].sort((a, b) => (a.period || '').localeCompare(b.period || ''))
  const maxPositive = Math.max(...sortedData.map(d => d.positive_count || 0), 1)
  const maxNegative = Math.max(...sortedData.map(d => d.negative_count || 0), 1)
  const maxY = Math.max(maxPositive, maxNegative, 1)
  const freqLabel = frequency === 'D' ? 'Day' : frequency === 'W' ? 'Week' : 'Month'

  const width = 560
  const height = 260
  const padding = { top: 28, right: 16, bottom: 32, left: 44 }
  const chartWidth = width - padding.left - padding.right
  const chartHeight = height - padding.top - padding.bottom

  const n = sortedData.length
  const xScale = (i) => padding.left + (n <= 1 ? chartWidth / 2 : (i / Math.max(n - 1, 1)) * chartWidth)
  const yScale = (v) => padding.top + chartHeight - (v / maxY) * chartHeight

  const positivePath = sortedData
    .map((d, i) => `${i === 0 ? 'M' : 'L'} ${xScale(i)} ${yScale(d.positive_count || 0)}`)
    .join(' ')
  const negativePath = sortedData
    .map((d, i) => `${i === 0 ? 'M' : 'L'} ${xScale(i)} ${yScale(d.negative_count || 0)}`)
    .join(' ')

  const tickCount = 5
  const yTicks = Array.from({ length: tickCount + 1 }, (_, i) => Math.round((maxY * i) / tickCount))

  const selectedRow = selectedIndex != null && sortedData[selectedIndex] ? sortedData[selectedIndex] : null
  const samples = selectedRow?.samples || []

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 space-y-3">
      <h5 className="text-sm font-semibold text-white">
        Sentiment over time: {themeName}
      </h5>
      <p className="text-xs text-gray-400">
        X = {freqLabel}, Y = count. Click a point to see counts and sample comments for that {freqLabel.toLowerCase()}.
      </p>

      <div className="flex gap-4 text-xs">
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-0.5 bg-green-500 rounded" />
          <span className="text-gray-300">Positive</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-0.5 bg-red-500 rounded" />
          <span className="text-gray-300">Negative</span>
        </span>
      </div>

      <svg width={width} height={height} className="overflow-visible">
        <text x={12} y={height / 2} textAnchor="middle" fill="#9ca3af" fontSize="10" transform={`rotate(-90, 12, ${height / 2})`}>
          Count
        </text>
        <line x1={padding.left} y1={padding.top} x2={padding.left} y2={padding.top + chartHeight} stroke="#4b5563" strokeWidth="1" />
        {yTicks.map((tick, i) => (
          <g key={i}>
            <line x1={padding.left} y1={yScale(tick)} x2={padding.left - 4} y2={yScale(tick)} stroke="#6b7280" strokeWidth="1" />
            <text x={padding.left - 6} y={yScale(tick)} textAnchor="end" dominantBaseline="middle" fill="#9ca3af" fontSize="10">{tick}</text>
          </g>
        ))}
        <line x1={padding.left} y1={padding.top + chartHeight} x2={padding.left + chartWidth} y2={padding.top + chartHeight} stroke="#4b5563" strokeWidth="1" />
        {sortedData.map((d, i) => {
          const showLabel = n <= 8 || i % Math.ceil(n / 8) === 0 || i === n - 1
          const label = (d.period || '').length > 10 ? (d.period || '').slice(0, 10) + '…' : (d.period || '')
          return showLabel ? (
            <text key={i} x={xScale(i)} y={height - 8} textAnchor="middle" fill="#9ca3af" fontSize="9">{label}</text>
          ) : null
        })}
        <path d={positivePath} fill="none" stroke="#22c55e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d={negativePath} fill="none" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        {sortedData.map((d, i) => {
          const x = xScale(i)
          const yPos = yScale(d.positive_count || 0)
          const yNeg = yScale(d.negative_count || 0)
          const isSelected = selectedIndex === i
          return (
            <g key={i}>
              <rect
                x={x - 12}
                y={padding.top}
                width={24}
                height={chartHeight}
                fill="transparent"
                style={{ cursor: 'pointer' }}
                onClick={() => setSelectedIndex(i)}
              />
              <circle cx={x} cy={yPos} r={isSelected ? 5 : 3} fill="#22c55e" stroke={isSelected ? '#fff' : 'none'} strokeWidth="1" style={{ cursor: 'pointer' }} onClick={() => setSelectedIndex(i)} />
              <circle cx={x} cy={yNeg} r={isSelected ? 5 : 3} fill="#ef4444" stroke={isSelected ? '#fff' : 'none'} strokeWidth="1" style={{ cursor: 'pointer' }} onClick={() => setSelectedIndex(i)} />
              <text x={x} y={yPos - 8} textAnchor="middle" fill="#22c55e" fontSize="10" fontWeight="600">{d.positive_count ?? 0}</text>
              <text x={x} y={yNeg + 14} textAnchor="middle" fill="#ef4444" fontSize="10" fontWeight="600">{d.negative_count ?? 0}</text>
            </g>
          )
        })}
      </svg>

      {selectedRow && (
        <div className="border-t border-gray-700 pt-3 mt-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-white">
              {selectedRow.period} — Positive: {selectedRow.positive_count ?? 0}, Negative: {selectedRow.negative_count ?? 0}, Neutral: {selectedRow.neutral_count ?? 0}
            </span>
            <button type="button" onClick={() => setSelectedIndex(null)} className="text-xs text-gray-400 hover:text-white">Clear</button>
          </div>
          {samples.length > 0 ? (
            <div className="space-y-2 max-h-48 overflow-y-auto">
              <p className="text-xs text-gray-400">Sample comments:</p>
              {samples.map((s, idx) => (
                <div key={idx} className="bg-gray-800 rounded p-2 text-sm">
                  <span className={`inline-block px-1.5 py-0.5 rounded text-xs font-medium mr-2 ${s.sentiment === 'positive' ? 'bg-green-600 text-white' : s.sentiment === 'negative' ? 'bg-red-600 text-white' : 'bg-gray-600 text-white'}`}>
                    {s.sentiment}
                  </span>
                  <span className="text-gray-200">{s.text}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-gray-500">No sample comments for this period.</p>
          )}
        </div>
      )}
    </div>
  )
}

export default ThemeSentimentOverTimeChart
