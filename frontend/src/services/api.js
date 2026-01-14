/**
 * API service for backend communication
 */
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('authToken')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  signup: async (username, email, password) => {
    const response = await api.post('/api/auth/signup', {
      username,
      email,
      password,
    })
    return response.data
  },

  login: async (username, password) => {
    const response = await api.post('/api/auth/login', {
      username,
      password,
    })
    return response.data
  },

  getCurrentUser: async () => {
    const response = await api.get('/api/auth/me')
    return response.data
  },
}

// File API
export const fileAPI = {
  upload: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/api/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },
}

// Analysis API
export const analysisAPI = {
  sentiment: async (fileId, useAI = false, dateStart = null, dateEnd = null, frequency = 'W') => {
    const response = await api.post('/api/analysis/sentiment', {
      file_id: fileId,
      use_ai: useAI,
      date_start: dateStart,
      date_end: dateEnd,
      frequency: frequency,
    })
    return response.data
  },

  themes: async (fileId, useAI = false, topK = 20, dateStart = null, dateEnd = null, useLDA = false) => {
    const response = await api.post('/api/analysis/themes', {
      file_id: fileId,
      use_ai: useAI,
      top_k: topK,
      date_start: dateStart,
      date_end: dateEnd,
      use_lda: useLDA,
    })
    return response.data
  },

  summaries: async (fileId, topK = 20, dateStart = null, dateEnd = null) => {
    const response = await api.post('/api/analysis/summaries', {
      file_id: fileId,
      top_k: topK,
      date_start: dateStart,
      date_end: dateEnd,
    })
    return response.data
  },

  trends: async (fileId, frequency = 'W', dateStart = null, dateEnd = null) => {
    const response = await api.post('/api/analysis/trends', {
      file_id: fileId,
      frequency: frequency,
      date_start: dateStart,
      date_end: dateEnd,
    })
    return response.data
  },

  semanticSearch: async (fileId, queryText, topK = 10, scoreThreshold = 0.5) => {
    const response = await api.post('/api/analysis/semantic-search', {
      file_id: fileId,
      query_text: queryText,
      top_k: topK,
      score_threshold: scoreThreshold,
    })
    return response.data
  },
}

// Async Processing API
export const asyncAPI = {
  startSentiment: async (fileId, useAI = false) => {
    const response = await api.post('/api/analysis/async/sentiment', {
      file_id: fileId,
      use_ai: useAI,
    })
    return response.data
  },

  getStatus: async (taskId) => {
    const response = await api.get(`/api/analysis/async/status/${taskId}`)
    return response.data
  },
}

// History API
export const historyAPI = {
  getFiles: async (limit = 100) => {
    const response = await api.get('/api/history/files', {
      params: { limit },
    })
    return response.data
  },

  getReports: async (limit = 100) => {
    const response = await api.get('/api/history/reports', {
      params: { limit },
    })
    return response.data
  },

  downloadReport: async (reportId) => {
    const response = await api.get(`/api/history/reports/${reportId}/download`, {
      responseType: 'blob',
    })
    return response
  },

  generateReport: async (fileId, options = {}) => {
    const response = await api.post('/api/reports/generate', {
      file_id: fileId,
      report_type: options.reportType || 'pdf',
      include_sentiment: options.includeSentiment !== false,
      include_themes: options.includeThemes !== false,
      include_summaries: options.includeSummaries !== false,
      include_priorities: options.includePriorities !== false,
      include_trends: options.includeTrends !== false,
      date_start: options.dateStart || null,
      date_end: options.dateEnd || null,
    })
    return response.data
  },
}

export default api

