import { useState, useEffect, useRef } from 'react'
import api from '../services/api'

const WordCloud = ({ 
  wordcloudPath, 
  title = "Word Cloud",
  description = "Word size = frequency × |sentiment|. Green = positive, Red = negative, Gray = neutral",
  className = ""
}) => {
  const [imageError, setImageError] = useState(false)
  const [imageLoading, setImageLoading] = useState(true)
  const [imageUrl, setImageUrl] = useState(null)
  const blobUrlRef = useRef(null)

  useEffect(() => {
    // Cleanup previous blob URL
    if (blobUrlRef.current) {
      URL.revokeObjectURL(blobUrlRef.current)
      blobUrlRef.current = null
    }

    if (!wordcloudPath) {
      setImageUrl(null)
      setImageLoading(false)
      setImageError(false)
      return
    }

    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const fullPath = wordcloudPath.startsWith('http') 
      ? wordcloudPath 
      : `${apiBaseUrl}${wordcloudPath}`

    // Fetch image with auth headers and create blob URL
    const fetchImage = async () => {
      try {
        setImageLoading(true)
        setImageError(false)
        
        const response = await api.get(fullPath, {
          responseType: 'blob',
          headers: {
            'Accept': 'image/png'
          }
        })
        
        // Create blob URL from response
        const blob = new Blob([response.data], { type: 'image/png' })
        const blobUrl = URL.createObjectURL(blob)
        blobUrlRef.current = blobUrl
        setImageUrl(blobUrl)
        setImageLoading(false)
      } catch (error) {
        console.error('Error loading wordcloud:', error)
        setImageError(true)
        setImageLoading(false)
        setImageUrl(null)
      }
    }

    fetchImage()

    // Cleanup blob URL on unmount or when wordcloudPath changes
    return () => {
      if (blobUrlRef.current) {
        URL.revokeObjectURL(blobUrlRef.current)
        blobUrlRef.current = null
      }
    }
  }, [wordcloudPath])

  if (!wordcloudPath) {
    return null
  }

  return (
    <div className={`pt-6 border-t border-gray-700 ${className}`}>
      <h4 className="font-semibold text-white mb-4">{title}</h4>
      
      {imageLoading && !imageError && (
        <div className="bg-white rounded-lg p-4 flex justify-center items-center min-h-[400px]">
          <div className="flex flex-col items-center gap-3">
            <svg className="animate-spin h-8 w-8 text-gray-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p className="text-sm text-gray-600">Loading word cloud...</p>
          </div>
        </div>
      )}

      {!imageLoading && !imageError && imageUrl && (
        <div className="bg-white rounded-lg p-4 flex justify-center">
          <img
            src={imageUrl}
            alt={title}
            className="max-w-full h-auto rounded shadow-lg"
            onError={(e) => {
              console.error('Image load error:', e)
              setImageError(true)
              setImageLoading(false)
            }}
          />
        </div>
      )}

      {imageError && (
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 text-center">
          <svg className="w-12 h-12 text-gray-500 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <p className="text-gray-400 text-sm">Word cloud image could not be loaded</p>
        </div>
      )}

      {description && !imageError && (
        <p className="text-xs text-gray-400 mt-2">{description}</p>
      )}
    </div>
  )
}

export default WordCloud

