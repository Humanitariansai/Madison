import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { GoogleOAuthProvider } from '@react-oauth/google'
import App from './App'
import './index.css'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''

// Always wrap with GoogleOAuthProvider to prevent hook errors
// If no client ID is provided, the component will handle it gracefully
const AppWrapper = () => {
  return (
    <GoogleOAuthProvider 
      clientId={GOOGLE_CLIENT_ID}
      // Use redirect mode to better show account picker
      // This will redirect the whole page instead of using a popup
    >
      <App />
    </GoogleOAuthProvider>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <AppWrapper />
    </BrowserRouter>
  </React.StrictMode>,
)

