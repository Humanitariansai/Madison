import { useMemo, useState, useEffect } from 'react'

const SentimentTemporalChart = ({ sentimentOverTime, trendMetrics, onFrequencyChange, currentFrequency = 'W' }) => {
  const [frequency, setFrequency] = useState(currentFrequency) // W = Weekly, D = Daily, M = Monthly
  
  // Update frequency when currentFrequency prop changes
  useEffect(() => {
    setFrequency(currentFrequency)
  }, [currentFrequency])

  // Process sentiment over time data
  const processedData = useMemo(() => {
    if (!sentimentOverTime || sentimentOverTime.length === 0) return null

    // Group by period and aggregate sentiment counts
    const periodMap = {}
    sentimentOverTime.forEach(item => {
      const period = item.period || 'all'
      const periodStr = typeof period === 'string' ? period : 
        (period.toISOString ? period.toISOString().split('T')[0] : String(period))
      
      if (!periodMap[periodStr]) {
        periodMap[periodStr] = {
          period: periodStr,
          positive: 0,
          negative: 0,
          neutral: 0,
          total: 0
        }
      }
      
      const label = item.sent_label || item.sentiment
      const count = item.count || 0
      
      if (label === 'positive') {
        periodMap[periodStr].positive += count
      } else if (label === 'negative') {
        periodMap[periodStr].negative += count
      } else if (label === 'neutral') {
        periodMap[periodStr].neutral += count
      }
      
      periodMap[periodStr].total += count
    })

    // Calculate percentages
    Object.values(periodMap).forEach(period => {
      if (period.total > 0) {
        period.positive_pct = (period.positive / period.total) * 100
        period.negative_pct = (period.negative / period.total) * 100
        period.neutral_pct = (period.neutral / period.total) * 100
        period.sentiment_index = period.positive_pct - period.negative_pct
      } else {
        period.positive_pct = 0
        period.negative_pct = 0
        period.neutral_pct = 0
        period.sentiment_index = 0
      }
    })

    return Object.values(periodMap).sort((a, b) => a.period.localeCompare(b.period))
  }, [sentimentOverTime])

  // Process trend metrics
  const trendData = useMemo(() => {
    if (!trendMetrics || trendMetrics.length === 0) return null

    return trendMetrics.map(item => ({
      period: item.period_str || item.period || 'all',
      positive: item.pos || 0,
      negative: item.neg || 0,
      neutral: item.neu || 0,
      total: item.total || 0,
      positive_pct: (item.pos_pct || 0) * 100,
      negative_pct: (item.neg_pct || 0) * 100,
      neutral_pct: (item.neu_pct || 0) * 100,
      sentiment_index: (item.sent_index || 0) * 100, // Convert to percentage
      sentiment_trend: (item.index_wow || 0) * 100,
      positive_trend: (item.pos_wow || 0) * 100,
      negative_trend: (item.neg_wow || 0) * 100,
      positive_ma: (item.pos_pct_ma || 0) * 100,
      negative_ma: (item.neg_pct_ma || 0) * 100,
      sentiment_ma: (item.index_ma || 0) * 100
    })).sort((a, b) => a.period.localeCompare(b.period))
  }, [trendMetrics])

  const displayData = trendData || processedData

  if (!displayData || displayData.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
        <p className="text-gray-400 text-sm">No temporal data available. Time column may be missing.</p>
      </div>
    )
  }

  const maxTotal = Math.max(...displayData.map(d => d.total || 0))

  return (
    <div className="space-y-6">
      {/* Sentiment Over Time Chart */}
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h5 className="text-sm font-semibold text-gray-300">Sentiment Over Time</h5>
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <span>Frequency:</span>
            <select
              value={frequency}
              onChange={(e) => {
                const newFreq = e.target.value
                setFrequency(newFreq)
                // Call callback if provided to trigger re-analysis
                if (onFrequencyChange) {
                  try {
                    onFrequencyChange(newFreq)
                  } catch (error) {
                    console.error('Error in frequency change callback:', error)
                  }
                }
              }}
              className="bg-gray-800 border border-gray-700 text-white rounded px-2 py-1 cursor-pointer hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50"
              title="Data is calculated weekly. Frequency selection is for display purposes."
            >
              <option value="W">Weekly</option>
              <option value="D">Daily</option>
              <option value="M">Monthly</option>
            </select>
          </div>
        </div>

        <div className="space-y-3">
          {displayData.map((data, idx) => {
            const sentimentColor = data.sentiment_index > 10
              ? 'text-green-400'
              : data.sentiment_index < -10
              ? 'text-red-400'
              : 'text-gray-400'

            const trendArrow = data.sentiment_trend > 1
              ? '↑'
              : data.sentiment_trend < -1
              ? '↓'
              : '→'

            return (
              <div key={idx} className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-400 font-medium">{data.period}</span>
                  <div className="flex items-center gap-3">
                    <span className="text-white">{data.total || 0} responses</span>
                    {data.sentiment_index !== undefined && (
                      <span className={sentimentColor}>
                        Index: {data.sentiment_index?.toFixed(1)}% {trendArrow}
                      </span>
                    )}
                  </div>
                </div>

                {/* Stacked bar showing sentiment distribution */}
                <div className="w-full bg-gray-800 rounded-full h-4 overflow-hidden flex">
                  {data.positive_pct > 0 && (
                    <div
                      className="bg-green-500 h-full transition-all duration-500 flex items-center justify-center"
                      style={{ width: `${data.positive_pct}%` }}
                      title={`Positive: ${data.positive_pct.toFixed(1)}%`}
                    >
                      {data.positive_pct > 5 && (
                        <span className="text-white text-xs font-medium">{data.positive_pct.toFixed(0)}%</span>
                      )}
                    </div>
                  )}
                  {data.neutral_pct > 0 && (
                    <div
                      className="bg-gray-500 h-full transition-all duration-500 flex items-center justify-center"
                      style={{ width: `${data.neutral_pct}%` }}
                      title={`Neutral: ${data.neutral_pct.toFixed(1)}%`}
                    >
                      {data.neutral_pct > 5 && (
                        <span className="text-white text-xs font-medium">{data.neutral_pct.toFixed(0)}%</span>
                      )}
                    </div>
                  )}
                  {data.negative_pct > 0 && (
                    <div
                      className="bg-red-500 h-full transition-all duration-500 flex items-center justify-center"
                      style={{ width: `${data.negative_pct}%` }}
                      title={`Negative: ${data.negative_pct.toFixed(1)}%`}
                    >
                      {data.negative_pct > 5 && (
                        <span className="text-white text-xs font-medium">{data.negative_pct.toFixed(0)}%</span>
                      )}
                    </div>
                  )}
                </div>

                {/* Detailed breakdown */}
                <div className="flex gap-4 text-xs">
                  <span className="text-green-400">
                    Pos: {data.positive || 0} ({data.positive_pct?.toFixed(1)}%)
                  </span>
                  <span className="text-gray-400">
                    Neu: {data.neutral || 0} ({data.neutral_pct?.toFixed(1)}%)
                  </span>
                  <span className="text-red-400">
                    Neg: {data.negative || 0} ({data.negative_pct?.toFixed(1)}%)
                  </span>
                </div>

                {/* Trend indicators */}
                {trendData && data.sentiment_trend !== undefined && (
                  <div className="flex gap-4 text-xs text-gray-500 pt-1 border-t border-gray-800">
                    <span>
                      Trend: {data.sentiment_trend > 0 ? '+' : ''}{data.sentiment_trend?.toFixed(2)}%
                    </span>
                    {data.sentiment_ma !== undefined && (
                      <span>
                        MA: {data.sentiment_ma?.toFixed(1)}%
                      </span>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Summary Statistics */}
      {trendData && trendData.length > 0 && (
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
          <h5 className="text-sm font-semibold text-gray-300 mb-3">Trend Summary</h5>
          <div className="grid grid-cols-3 gap-4 text-xs">
            <div>
              <div className="text-gray-400 mb-1">Overall Sentiment</div>
              <div className="text-white font-semibold">
                {trendData[trendData.length - 1]?.sentiment_index?.toFixed(1)}%
              </div>
            </div>
            <div>
              <div className="text-gray-400 mb-1">Latest Trend</div>
              <div className={`font-semibold ${
                trendData[trendData.length - 1]?.sentiment_trend > 0
                  ? 'text-green-400'
                  : trendData[trendData.length - 1]?.sentiment_trend < 0
                  ? 'text-red-400'
                  : 'text-gray-400'
              }`}>
                {trendData[trendData.length - 1]?.sentiment_trend > 0 ? '+' : ''}
                {trendData[trendData.length - 1]?.sentiment_trend?.toFixed(2)}%
              </div>
            </div>
            <div>
              <div className="text-gray-400 mb-1">Periods Analyzed</div>
              <div className="text-white font-semibold">{trendData.length}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SentimentTemporalChart

