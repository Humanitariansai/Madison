import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import SurveyAnalysis from './SurveyAnalysis'
import History from './History'
import { authAPI } from '../services/api'

const Dashboard = () => {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [activePage, setActivePage] = useState('analysis')

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('authToken')
      if (!token) {
        navigate('/login')
        return
      }

      // Try to get user info from backend
      try {
        const userData = await authAPI.getCurrentUser()
        setUser(userData)
        localStorage.setItem('user', JSON.stringify(userData))
      } catch (err) {
        // If backend auth fails, use local storage data
        const storedUser = localStorage.getItem('user')
        if (storedUser) {
          setUser(JSON.parse(storedUser))
        } else {
          // Fallback to local storage
          setUser({
            username: localStorage.getItem('userName') || 'User',
            email: localStorage.getItem('userEmail') || '',
          })
        }
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()
  }, [navigate])

  const handleLogout = () => {
    localStorage.removeItem('authToken')
    localStorage.removeItem('user')
    localStorage.removeItem('userEmail')
    localStorage.removeItem('userName')
    
    // Clear Google OAuth session by revoking token
    const token = localStorage.getItem('authToken')
    if (token && token.startsWith('ya29.')) {
      // Only revoke if it's a Google token
      fetch(`https://oauth2.googleapis.com/revoke?token=${token}`, {
        method: 'POST',
        headers: {
          'Content-type': 'application/x-www-form-urlencoded',
        },
      }).catch(() => {
        // Ignore errors if token is already invalid
      })
    }
    
    navigate('/login')
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    )
  }

  const userName = user?.username || user?.name || localStorage.getItem('userName') || 'User'
  const userEmail = user?.email || localStorage.getItem('userEmail') || ''

  return (
    <div className="min-h-screen bg-black">
      {/* Top Navigation Bar */}
      <div className="bg-white border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-black">Humanitarians AI</h1>
              <span className="text-gray-400">|</span>
              <nav className="flex space-x-1">
                <button
                  onClick={() => setActivePage('analysis')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    activePage === 'analysis'
                      ? 'bg-black text-white'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  Analysis
                </button>
                <button
                  onClick={() => setActivePage('history')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    activePage === 'history'
                      ? 'bg-black text-white'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  History
                </button>
              </nav>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-medium text-black">{userName}</p>
                <p className="text-xs text-gray-500">{userEmail}</p>
              </div>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-black text-white rounded-lg font-semibold hover:bg-gray-800 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      {activePage === 'analysis' ? <SurveyAnalysis /> : <History />}
    </div>
  )
}

export default Dashboard
