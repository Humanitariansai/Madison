import { useMemo, useState } from 'react'

const ThemeTemporalChart = ({ themeTemporal, overallTrends }) => {
  const [selectedTheme, setSelectedTheme] = useState(null)

  const themes = useMemo(() => {
    if (!themeTemporal || themeTemporal.length === 0) return []
    const uniqueThemes = [...new Set(themeTemporal.map(t => t.keyphrase))]
    return uniqueThemes
  }, [themeTemporal])

  const filteredData = useMemo(() => {
    if (!themeTemporal || themeTemporal.length === 0) return []
    if (!selectedTheme) return themeTemporal
    return themeTemporal.filter(t => t.keyphrase === selectedTheme)
  }, [themeTemporal, selectedTheme])

  const chartData = useMemo(() => {
    if (!filteredData || filteredData.length === 0) return []
    
    // Group by period and aggregate
    const periodMap = {}
    filteredData.forEach(item => {
      const period = item.period || 'all'
      if (!periodMap[period]) {
        periodMap[period] = {
          period,
          mention_count: 0,
          positive_count: 0,
          negative_count: 0,
          neutral_count: 0,
          avg_sentiment: 0,
          sentiment_sum: 0,
          count: 0
        }
      }
      periodMap[period].mention_count += item.mention_count || 0
      periodMap[period].positive_count += item.positive_count || 0
      periodMap[period].negative_count += item.negative_count || 0
      periodMap[period].neutral_count += item.neutral_count || 0
      periodMap[period].sentiment_sum += (item.avg_sentiment || 0) * (item.mention_count || 0)
      periodMap[period].count += item.mention_count || 0
    })

    // Calculate average sentiment
    Object.values(periodMap).forEach(period => {
      period.avg_sentiment = period.count > 0 ? period.sentiment_sum / period.count : 0
    })

    return Object.values(periodMap).sort((a, b) => a.period.localeCompare(b.period))
  }, [filteredData])

  if (chartData.length === 0 && !overallTrends) return null

  const maxMentions = Math.max(
    ...chartData.map(d => d.mention_count || 0),
    ...(overallTrends?.map(t => t.total_mentions || 0) || [0])
  )

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h5 className="text-sm font-semibold text-gray-300">
          {selectedTheme ? `Theme: ${selectedTheme}` : 'Overall Theme Trends'}
        </h5>
        {themes.length > 0 && (
          <select
            value={selectedTheme || ''}
            onChange={(e) => setSelectedTheme(e.target.value || null)}
            className="bg-gray-900 border border-gray-700 text-white text-xs rounded px-2 py-1"
          >
            <option value="">All Themes</option>
            {themes.map((theme, idx) => (
              <option key={idx} value={theme}>{theme}</option>
            ))}
          </select>
        )}
      </div>

      {/* Overall Trends Section */}
      {overallTrends && overallTrends.length > 0 && (
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 space-y-3">
          <h6 className="text-xs font-semibold text-gray-300 mb-2">Overall Theme Trends</h6>
          {overallTrends.map((trend, idx) => {
            const sentimentColor = trend.avg_sentiment > 0.1 
              ? 'text-green-400' 
              : trend.avg_sentiment < -0.1 
              ? 'text-red-400' 
              : 'text-gray-400'
            
            return (
              <div key={idx} className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-400">{trend.period}</span>
                  <div className="flex items-center gap-3">
                    <span className="text-white">{trend.total_mentions} mentions</span>
                    <span className={sentimentColor}>
                      Sentiment: {trend.avg_sentiment?.toFixed(3)}
                    </span>
                  </div>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-white h-full transition-all duration-500"
                    style={{ width: `${((trend.total_mentions || 0) / maxMentions) * 100}%` }}
                  />
                </div>
                <div className="flex gap-4 text-xs">
                  <span className="text-green-400">Pos: {trend.total_positive || 0}</span>
                  <span className="text-red-400">Neg: {trend.total_negative || 0}</span>
                  <span className="text-gray-400">Neu: {trend.total_neutral || 0}</span>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Individual Theme Trends */}
      {chartData.length > 0 && (
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 space-y-3">
          <h6 className="text-xs font-semibold text-gray-300 mb-2">
            {selectedTheme ? `${selectedTheme} Over Time` : 'Themes Over Time'}
          </h6>
          {chartData.map((data, idx) => {
            const sentimentColor = data.avg_sentiment > 0.1 
              ? 'text-green-400' 
              : data.avg_sentiment < -0.1 
              ? 'text-red-400' 
              : 'text-gray-400'
            
            const trendArrow = data.sentiment_trend > 0.01 
              ? '↑' 
              : data.sentiment_trend < -0.01 
              ? '↓' 
              : '→'
            
            return (
              <div key={idx} className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-400">{data.period}</span>
                  <div className="flex items-center gap-3">
                    <span className="text-white">{data.mention_count} mentions</span>
                    <span className={sentimentColor}>
                      {data.avg_sentiment?.toFixed(3)} {trendArrow}
                    </span>
                  </div>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-white h-full transition-all duration-500"
                    style={{ width: `${((data.mention_count || 0) / maxMentions) * 100}%` }}
                  />
                </div>
                <div className="flex gap-4 text-xs">
                  <span className="text-green-400">Pos: {data.positive_count || 0} ({data.positive_pct?.toFixed(1)}%)</span>
                  <span className="text-red-400">Neg: {data.negative_count || 0} ({data.negative_pct?.toFixed(1)}%)</span>
                  <span className="text-gray-400">Neu: {data.neutral_count || 0}</span>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default ThemeTemporalChart

