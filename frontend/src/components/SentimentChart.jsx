import { useMemo } from 'react'

const SentimentChart = ({ sentimentData }) => {
  const chartData = useMemo(() => {
    if (!sentimentData?.sentiment_distribution) return null
    
    const { positive = 0, negative = 0, neutral = 0 } = sentimentData.sentiment_distribution
    const total = positive + negative + neutral
    
    if (total === 0) return null
    
    return {
      positive: { count: positive, pct: (positive / total) * 100 },
      negative: { count: negative, pct: (negative / total) * 100 },
      neutral: { count: neutral, pct: (neutral / total) * 100 },
      total
    }
  }, [sentimentData])

  if (!chartData) return null

  return (
    <div className="space-y-4">
      {/* Bar Chart */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">Positive</span>
          <span className="text-white font-medium">{chartData.positive.count.toLocaleString()} ({chartData.positive.pct.toFixed(1)}%)</span>
        </div>
        <div className="w-full bg-gray-900 rounded-full h-6 overflow-hidden">
          <div
            className="bg-white h-full flex items-center justify-end pr-2 transition-all duration-500"
            style={{ width: `${chartData.positive.pct}%` }}
          >
            {chartData.positive.pct > 5 && (
              <span className="text-black text-xs font-medium">{chartData.positive.pct.toFixed(1)}%</span>
            )}
          </div>
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">Neutral</span>
          <span className="text-white font-medium">{chartData.neutral.count.toLocaleString()} ({chartData.neutral.pct.toFixed(1)}%)</span>
        </div>
        <div className="w-full bg-gray-900 rounded-full h-6 overflow-hidden">
          <div
            className="bg-gray-500 h-full flex items-center justify-end pr-2 transition-all duration-500"
            style={{ width: `${chartData.neutral.pct}%` }}
          >
            {chartData.neutral.pct > 5 && (
              <span className="text-white text-xs font-medium">{chartData.neutral.pct.toFixed(1)}%</span>
            )}
          </div>
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">Negative</span>
          <span className="text-white font-medium">{chartData.negative.count.toLocaleString()} ({chartData.negative.pct.toFixed(1)}%)</span>
        </div>
        <div className="w-full bg-gray-900 rounded-full h-6 overflow-hidden">
          <div
            className="bg-gray-700 h-full flex items-center justify-end pr-2 transition-all duration-500"
            style={{ width: `${chartData.negative.pct}%` }}
          >
            {chartData.negative.pct > 5 && (
              <span className="text-white text-xs font-medium">{chartData.negative.pct.toFixed(1)}%</span>
            )}
          </div>
        </div>
      </div>

      {/* Pie Chart Representation */}
      <div className="pt-4 border-t border-gray-700">
        <div className="flex items-center justify-center">
          <div className="relative w-48 h-48">
            <svg viewBox="0 0 100 100" className="transform -rotate-90">
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="#374151"
                strokeWidth="20"
              />
              {chartData.positive.pct > 0 && (
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  fill="none"
                  stroke="#ffffff"
                  strokeWidth="20"
                  strokeDasharray={`${2 * Math.PI * 40 * (chartData.positive.pct / 100)} ${2 * Math.PI * 40}`}
                  strokeDashoffset="0"
                  className="transition-all duration-500"
                />
              )}
              {chartData.neutral.pct > 0 && (
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  fill="none"
                  stroke="#6b7280"
                  strokeWidth="20"
                  strokeDasharray={`${2 * Math.PI * 40 * (chartData.neutral.pct / 100)} ${2 * Math.PI * 40}`}
                  strokeDashoffset={`-${2 * Math.PI * 40 * (chartData.positive.pct / 100)}`}
                  className="transition-all duration-500"
                />
              )}
              {chartData.negative.pct > 0 && (
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  fill="none"
                  stroke="#4b5563"
                  strokeWidth="20"
                  strokeDasharray={`${2 * Math.PI * 40 * (chartData.negative.pct / 100)} ${2 * Math.PI * 40}`}
                  strokeDashoffset={`-${2 * Math.PI * 40 * ((chartData.positive.pct + chartData.neutral.pct) / 100)}`}
                  className="transition-all duration-500"
                />
              )}
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="text-2xl font-bold text-white">{chartData.total.toLocaleString()}</div>
                <div className="text-xs text-gray-400">Total</div>
              </div>
            </div>
          </div>
        </div>
        <div className="flex justify-center gap-6 mt-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-white rounded"></div>
            <span className="text-xs text-gray-400">Positive</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-gray-500 rounded"></div>
            <span className="text-xs text-gray-400">Neutral</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-gray-700 rounded"></div>
            <span className="text-xs text-gray-400">Negative</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SentimentChart

