import { useMemo } from 'react'

const ThemePriorityChart = ({ priorities }) => {
  const topPriorities = useMemo(() => {
    if (!priorities || priorities.length === 0) return []
    return priorities.slice(0, 10).sort((a, b) => (b.priority || 0) - (a.priority || 0))
  }, [priorities])

  if (topPriorities.length === 0) return null

  const maxPriority = Math.max(...topPriorities.map(p => p.priority || 0))

  return (
    <div className="space-y-3">
      {topPriorities.map((priority, idx) => {
        const priorityValue = priority.priority || 0
        const percentage = maxPriority > 0 ? (priorityValue / maxPriority) * 100 : 0
        
        return (
          <div key={idx} className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="text-white font-medium truncate flex-1 mr-2">
                {priority.keyphrase || priority.theme}
              </span>
              <div className="flex items-center gap-3 text-xs">
                {priority.count && (
                  <span className="text-gray-400">Count: {priority.count}</span>
                )}
                {priority.neg_share !== undefined && (
                  <span className="text-gray-400">
                    Neg: {(priority.neg_share * 100).toFixed(1)}%
                  </span>
                )}
                <span className="text-white font-semibold">
                  Priority: {priorityValue.toFixed(2)}
                </span>
              </div>
            </div>
            <div className="w-full bg-gray-900 rounded-full h-3 overflow-hidden">
              <div
                className="bg-white h-full transition-all duration-500"
                style={{ width: `${percentage}%` }}
              />
            </div>
            <div className="flex gap-2 flex-wrap">
              {priority.recency !== undefined && (
                <span className="text-xs px-2 py-1 bg-gray-800 rounded text-gray-400">
                  Recency: {(priority.recency * 100).toFixed(0)}%
                </span>
              )}
              {priority.trend !== undefined && (
                <span className={`text-xs px-2 py-1 bg-gray-800 rounded ${
                  priority.trend > 0 ? 'text-red-400' : priority.trend < 0 ? 'text-green-400' : 'text-gray-400'
                }`}>
                  Trend: {priority.trend > 0 ? '↑' : priority.trend < 0 ? '↓' : '→'} {Math.abs(priority.trend).toFixed(2)}
                </span>
              )}
              {priority.effort !== undefined && (
                <span className="text-xs px-2 py-1 bg-gray-800 rounded text-gray-400">
                  Effort: {(priority.effort * 100).toFixed(0)}%
                </span>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default ThemePriorityChart

