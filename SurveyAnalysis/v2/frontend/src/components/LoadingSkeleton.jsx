const LoadingSkeleton = ({ type = 'default' }) => {
  if (type === 'card') {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 animate-pulse">
        <div className="h-6 bg-gray-700 rounded w-1/3 mb-4"></div>
        <div className="space-y-3">
          <div className="h-4 bg-gray-700 rounded w-full"></div>
          <div className="h-4 bg-gray-700 rounded w-5/6"></div>
          <div className="h-4 bg-gray-700 rounded w-4/6"></div>
        </div>
      </div>
    )
  }

  if (type === 'table') {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="bg-gray-800 border border-gray-700 rounded-lg p-4 animate-pulse">
            <div className="h-4 bg-gray-700 rounded w-3/4 mb-2"></div>
            <div className="h-3 bg-gray-700 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    )
  }

  if (type === 'chart') {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 animate-pulse">
        <div className="h-6 bg-gray-700 rounded w-1/4 mb-6"></div>
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i}>
              <div className="h-4 bg-gray-700 rounded w-1/3 mb-2"></div>
              <div className="h-6 bg-gray-700 rounded w-full"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="animate-pulse">
      <div className="h-4 bg-gray-700 rounded w-3/4 mb-2"></div>
      <div className="h-4 bg-gray-700 rounded w-1/2"></div>
    </div>
  )
}

export default LoadingSkeleton

