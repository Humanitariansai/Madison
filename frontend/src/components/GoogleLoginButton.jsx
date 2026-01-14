import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

const GoogleLoginButton = ({ onLoadingChange, onError, onSuccess, disabled }) => {
  const navigate = useNavigate()
  const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID
  const redirectUri = window.location.origin

  // Handle OAuth callback when redirected back
  useEffect(() => {
    const handleOAuthCallback = async () => {
      const hash = window.location.hash.substring(1)
      const params = new URLSearchParams(hash)
      const accessToken = params.get('access_token')
      const error = params.get('error')
      const returnedState = params.get('state')
      const storedState = sessionStorage.getItem('oauth_state')

      console.log('OAuth callback detected:', { 
        hasToken: !!accessToken, 
        hasError: !!error, 
        returnedState, 
        storedState,
        match: returnedState === storedState
      })

      if (error) {
        console.error('Google OAuth error:', error)
        onError(`Google login error: ${error}`)
        onLoadingChange(false)
        // Clean up URL
        window.history.replaceState({}, document.title, '/login')
        return
      }

      if (accessToken) {
        if (returnedState && returnedState !== storedState) {
          console.error('State mismatch:', { returnedState, storedState })
          onError('Security check failed. Please try again.')
          onLoadingChange(false)
          window.history.replaceState({}, document.title, '/login')
          return
        }

        try {
          onLoadingChange(true)
          onError('')
          
          console.log('Sending Google token to backend...')
          
          // Send Google token to backend for authentication
          const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
          const response = await axios.post(
            `${API_BASE_URL}/api/auth/google`,
            { google_token: accessToken },
            {
              headers: {
                'Content-Type': 'application/json'
              }
            }
          )

          console.log('Backend response received:', response.data)

          // Store backend JWT token and user info
          localStorage.setItem('authToken', response.data.access_token)
          localStorage.setItem('user', JSON.stringify(response.data.user))
          localStorage.setItem('userEmail', response.data.user.email || '')
          localStorage.setItem('userName', response.data.user.username || response.data.user.email || 'User')
          
          // Clean up
          sessionStorage.removeItem('oauth_state')
          window.history.replaceState({}, document.title, '/login')
          
          console.log('Navigating to dashboard...')
          
          // Pass userInfo to onSuccess callback (which will navigate)
          onSuccess(response.data.user)
        } catch (err) {
          console.error('Google login error:', err)
          const errorMsg = err.response?.data?.detail || err.response?.data?.message || 'Google login failed.'
          onError(errorMsg)
          onLoadingChange(false)
          window.history.replaceState({}, document.title, '/login')
        }
      }
    }

    // Check if we have OAuth parameters in URL hash
    const hash = window.location.hash
    if (hash && (hash.includes('access_token') || hash.includes('error'))) {
      console.log('OAuth callback detected in URL hash:', hash.substring(0, 50) + '...')
      handleOAuthCallback()
    }
  }, []) // Empty deps - only run once on mount

  const handleGoogleLogin = () => {
    if (!GOOGLE_CLIENT_ID) {
      onError('Google Client ID is not configured.')
      return
    }

    try {
      onLoadingChange(true)
      onError('')

      // Manually construct OAuth URL with prompt=select_account
      const scope = 'openid email profile'
      const responseType = 'token'
      const state = `state_${Date.now()}_${Math.random()}`
      
      // Store state to verify later
      sessionStorage.setItem('oauth_state', state)
      
      // Redirect to login page to ensure callback handler is available
      const redirectUriWithPath = `${redirectUri}/login`
      
      const authUrl = new URL('https://accounts.google.com/o/oauth2/v2/auth')
      authUrl.searchParams.set('client_id', GOOGLE_CLIENT_ID)
      authUrl.searchParams.set('redirect_uri', redirectUriWithPath)
      authUrl.searchParams.set('response_type', responseType)
      authUrl.searchParams.set('scope', scope)
      authUrl.searchParams.set('state', state)
      // CRITICAL: Force account selection - this will show the account picker
      authUrl.searchParams.set('prompt', 'select_account')
      // Access type
      authUrl.searchParams.set('access_type', 'online')

      console.log('Redirecting to Google OAuth with account picker')
      console.log('Auth URL:', authUrl.toString())
      console.log('Redirect URI:', redirectUriWithPath)

      // Redirect to Google OAuth (this will show the account picker)
      window.location.href = authUrl.toString()

    } catch (err) {
      console.error('Error initiating Google login:', err)
      onError('Failed to start Google login. Please try again.')
      onLoadingChange(false)
    }
  }

  return (
    <button
      type="button"
      onClick={handleGoogleLogin}
      disabled={disabled}
      className="w-full flex items-center justify-center gap-3 px-4 py-3 border-2 border-gray-700 rounded-lg font-medium text-gray-300 bg-gray-800 hover:bg-gray-700 hover:border-gray-600 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <svg className="w-5 h-5" viewBox="0 0 24 24">
        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
      </svg>
      Continue with Google
    </button>
  )
}

export default GoogleLoginButton
