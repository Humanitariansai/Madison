import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useEffect } from 'react'
import LoginPage from './pages/LoginPage'
import Dashboard from './pages/Dashboard'

// Protected Route component
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('authToken')
  return token ? children : <Navigate to="/login" replace />
}

// Root redirect component that checks for OAuth callback
const RootRedirect = () => {
  const location = useLocation()
  
  // If there's an OAuth callback in the hash, redirect to login page to handle it
  useEffect(() => {
    if (location.hash && (location.hash.includes('access_token') || location.hash.includes('error'))) {
      // Redirect to login page with the hash so the callback handler can process it
      window.location.href = `/login${location.hash}`
      return
    }
  }, [location])
  
  return <Navigate to="/login" replace />
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<RootRedirect />} />
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

export default App
