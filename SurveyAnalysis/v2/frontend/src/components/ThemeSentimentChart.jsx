import { useMemo } from 'react'

const ThemeSentimentChart = ({ themeSentiment }) => {
  const sortedThemes = useMemo(() => {
    if (!themeSentiment || themeSentiment.length === 0) return []
    return [...themeSentiment].sort((a, b) => (b.total_mentions || 0) - (a.total_mentions || 0)).slice(0, 10)
  }, [themeSentiment])

  if (sortedThemes.length === 0) return null

  return (
    <div className="space-y-4">
      <h5 className="text-sm font-semibold text-gray-300 mb-3">Theme Sentiment Analysis</h5>
      {sortedThemes.map((theme, idx) => {
        const { keyphrase, total_mentions, positive_pct, negative_pct, neutral_pct, avg_sentiment, dominant_sentiment } = theme
        
        const sentimentColor = avg_sentiment > 0.1 
          ? 'text-green-400' 
          : avg_sentiment < -0.1 
          ? 'text-red-400' 
          : 'text-gray-400'
        
        const dominantColor = dominant_sentiment === 'positive'
          ? 'bg-green-500'
          : dominant_sentiment === 'negative'
          ? 'bg-red-500'
          : 'bg-gray-500'

        return (
          <div key={idx} className="bg-gray-900 border border-gray-700 rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <span className="text-white font-medium text-sm truncate">{keyphrase}</span>
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${dominantColor} text-white`}>
                  {dominant_sentiment}
                </span>
              </div>
              <span className="text-xs text-gray-400 ml-2 whitespace-nowrap">
                {total_mentions} mentions
              </span>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400">Positive</span>
                <span className="text-white">{positive_pct?.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-green-500 h-full transition-all duration-500"
                  style={{ width: `${positive_pct || 0}%` }}
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400">Negative</span>
                <span className="text-white">{negative_pct?.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-red-500 h-full transition-all duration-500"
                  style={{ width: `${negative_pct || 0}%` }}
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400">Neutral</span>
                <span className="text-white">{neutral_pct?.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-gray-500 h-full transition-all duration-500"
                  style={{ width: `${neutral_pct || 0}%` }}
                />
              </div>
            </div>

            <div className="pt-2 border-t border-gray-700">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400">Avg. Sentiment:</span>
                <span className={`font-semibold ${sentimentColor}`}>
                  {avg_sentiment?.toFixed(3)} 
                  {avg_sentiment > 0.1 && ' ↑'}
                  {avg_sentiment < -0.1 && ' ↓'}
                </span>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default ThemeSentimentChart

