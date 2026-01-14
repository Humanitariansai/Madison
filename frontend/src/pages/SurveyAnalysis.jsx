import { useState, useEffect } from 'react'
import { fileAPI, analysisAPI, asyncAPI, historyAPI } from '../services/api'
import SentimentChart from '../components/SentimentChart'
import SentimentTemporalChart from '../components/SentimentTemporalChart'
import ThemePriorityChart from '../components/ThemePriorityChart'
import ThemeSentimentChart from '../components/ThemeSentimentChart'
import ThemeTemporalChart from '../components/ThemeTemporalChart'
import LoadingSkeleton from '../components/LoadingSkeleton'
import WordCloud from '../components/WordCloud'

const SurveyAnalysis = () => {
  const [uploadedFile, setUploadedFile] = useState(null)
  const [fileData, setFileData] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [useAI, setUseAI] = useState(false)
  const [useLDA, setUseLDA] = useState(false)
  const [sentimentData, setSentimentData] = useState(null)
  const [themesData, setThemesData] = useState(null)
  const [summariesData, setSummariesData] = useState(null)
  const [trendsData, setTrendsData] = useState(null)
  const [semanticSearchData, setSemanticSearchData] = useState(null)
  const [wordcloudData, setWordcloudData] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [activeTab, setActiveTab] = useState('upload')
  const [activeAnalysis, setActiveAnalysis] = useState(null) // 'sentiment', 'themes', 'summaries', 'trends', 'semantic-search', 'wordcloud'
  const [isReportLoading, setIsReportLoading] = useState(false) // Separate loading state for report generation
  const [trendsFrequency, setTrendsFrequency] = useState('W') // W = Weekly, D = Daily, M = Monthly
  const [dateStart, setDateStart] = useState('')
  const [dateEnd, setDateEnd] = useState('')
  const [sentimentFrequency, setSentimentFrequency] = useState('W') // W = Weekly, D = Daily, M = Monthly
  
  // Async processing state
  const [asyncTaskId, setAsyncTaskId] = useState(null)
  const [asyncProgress, setAsyncProgress] = useState(0)
  const [asyncStatus, setAsyncStatus] = useState(null)

  // Poll async task status
  useEffect(() => {
    if (!asyncTaskId) return

    const interval = setInterval(async () => {
      try {
        const status = await asyncAPI.getStatus(asyncTaskId)
        setAsyncStatus(status)
        setAsyncProgress(status.progress || 0)

        if (status.status === 'SUCCESS') {
          setSentimentData(status.result)
          setActiveAnalysis('sentiment') // Show sentiment results
          setAsyncTaskId(null)
          setSuccess('Analysis completed successfully!')
        } else if (status.status === 'FAILURE') {
          setError(status.error || 'Analysis failed')
          setActiveAnalysis(null) // Clear on failure
          setAsyncTaskId(null)
        }
      } catch (err) {
        console.error('Error checking async status:', err)
      }
    }, 2000) // Poll every 2 seconds

    return () => clearInterval(interval)
  }, [asyncTaskId])

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setIsLoading(true)
    setError('')
    setSuccess('')

    try {
      const response = await fileAPI.upload(file)
      setFileData(response)
      setUploadedFile(file)
      setSuccess('File uploaded successfully!')
      
      // Check if large file
      if (response.rows_count > 100000) {
        setSuccess(`Large file detected (${response.rows_count.toLocaleString()} rows). Consider using async processing for analysis.`)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'File upload failed')
    } finally {
      setIsLoading(false)
    }
  }

  const handleAnalyzeSentiment = async (useAsync = false) => {
    if (!fileData) return

    setIsLoading(true)
    setError('')
    setSuccess('')
    setSentimentData(null)
    setActiveAnalysis('sentiment') // Set active analysis

    // Use async for large files (>100k rows)
    const isLargeFile = fileData.rows_count > 100000

    try {
      console.log('Analyzing sentiment with:', { useAI, fileId: fileData.file_id })
      if (useAsync || isLargeFile) {
        const task = await asyncAPI.startSentiment(fileData.file_id, useAI)
        setAsyncTaskId(task.task_id)
        setSuccess('Analysis started in background. Progress will be shown below.')
      } else {
        const response = await analysisAPI.sentiment(
          fileData.file_id,
          useAI,
          dateStart || null,
          dateEnd || null,
          sentimentFrequency
        )
        console.log('Sentiment response:', response)
        setSentimentData(response)
        setSuccess(`Sentiment analysis completed! ${useAI ? '(AI)' : '(VADER)'}`)
      }
    } catch (err) {
      console.error('Sentiment analysis error:', err)
      setError(err.response?.data?.detail || 'Sentiment analysis failed')
      setActiveAnalysis(null) // Clear on error
    } finally {
      setIsLoading(false)
    }
  }

  const handleExtractThemes = async () => {
    if (!fileData) return

    setIsLoading(true)
    setError('')
    setSuccess('')
    setThemesData(null)
    setActiveAnalysis('themes') // Set active analysis

    try {
      const response = await analysisAPI.themes(
        fileData.file_id,
        useAI,
        20,
        dateStart || null,
        dateEnd || null,
        useLDA
      )
      setThemesData(response)
      const method = useLDA ? 'LDA Topic Modeling' : useAI ? 'AI (OpenAI)' : 'YAKE/TF-IDF'
      setSuccess(`Theme extraction completed using ${method}!`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Theme extraction failed')
      setActiveAnalysis(null) // Clear on error
    } finally {
      setIsLoading(false)
    }
  }

  const handleGenerateSummaries = async () => {
    if (!fileData) return

    setIsLoading(true)
    setError('')
    setSuccess('')
    setSummariesData(null)
    setActiveAnalysis('summaries') // Set active analysis

    try {
      const response = await analysisAPI.summaries(
        fileData.file_id,
        20,
        dateStart || null,
        dateEnd || null
      )
      setSummariesData(response)
      setSuccess('Summaries generated successfully!')
    } catch (err) {
      setError(err.response?.data?.detail || 'Summary generation failed')
      setActiveAnalysis(null) // Clear on error
    } finally {
      setIsLoading(false)
    }
  }

  const handleAnalyzeTrends = async (frequency = null) => {
    if (!fileData) {
      console.error('handleAnalyzeTrends: No file data available')
      setError('Please upload a file first')
      return
    }

    const freq = frequency || trendsFrequency
    console.log('handleAnalyzeTrends called with:', { fileId: fileData.file_id, frequency: freq, dateStart, dateEnd })

    setIsLoading(true)
    setError('')
    setSuccess('')
    setTrendsData(null)
    setActiveAnalysis('trends') // Set active analysis

    try {
      console.log('Calling analysisAPI.trends...')
      const response = await analysisAPI.trends(
        fileData.file_id,
        freq,
        dateStart || null,
        dateEnd || null
      )
      console.log('Trends API response:', response)
      setTrendsData(response)
      setSuccess(`Trends analysis completed with ${freq === 'D' ? 'Daily' : freq === 'M' ? 'Monthly' : 'Weekly'} frequency!`)
    } catch (err) {
      console.error('Trends analysis error:', err)
      console.error('Error details:', err.response?.data)
      setError(err.response?.data?.detail || err.message || 'Trends analysis failed')
      setActiveAnalysis(null) // Clear on error
    } finally {
      setIsLoading(false)
    }
  }

  const handleSemanticSearch = async () => {
    if (!fileData || !searchQuery.trim()) {
      setError('Please enter a search query')
      return
    }

    setIsLoading(true)
    setError('')
    setSuccess('')
    setSemanticSearchData(null)
    setActiveAnalysis('semantic-search') // Set active analysis

    try {
      const response = await analysisAPI.semanticSearch(
        fileData.file_id,
        searchQuery,
        10,
        0.5
      )
      setSemanticSearchData(response)
      setSuccess(`Found ${response.total_found} similar responses`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Semantic search failed')
      setActiveAnalysis(null) // Clear on error
    } finally {
      setIsLoading(false)
    }
  }

  const handleGenerateWordCloud = async () => {
    if (!fileData) return

    setIsLoading(true)
    setError('')
    setSuccess('')
    setWordcloudData(null)
    setActiveAnalysis('wordcloud') // Set active analysis

    try {
      // Generate wordcloud by running sentiment analysis (which includes wordcloud generation)
      const response = await analysisAPI.sentiment(
        fileData.file_id,
        useAI,
        dateStart || null,
        dateEnd || null,
        sentimentFrequency
      )
      
      // Extract wordcloud data from sentiment response
      if (response.wordcloud_path) {
        setWordcloudData({
          wordcloud_path: response.wordcloud_path,
          type: 'sentiment',
          sentiment_distribution: response.sentiment_distribution
        })
        setSuccess('Word cloud generated successfully!')
      } else {
        setError('Word cloud could not be generated. Please try again.')
        setActiveAnalysis(null)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Word cloud generation failed')
      setActiveAnalysis(null) // Clear on error
    } finally {
      setIsLoading(false)
    }
  }

  const handleGenerateReport = async (reportType = 'pdf') => {
    if (!fileData) return

    setIsReportLoading(true)
    setError('')
    setSuccess('')

    try {
      const report = await historyAPI.generateReport(fileData.file_id, {
        reportType,
        includeSentiment: true,
        includeThemes: true,
        includeSummaries: true,
        includePriorities: true,
        includeTrends: true,
        dateStart: dateStart || null,
        dateEnd: dateEnd || null,
      })

      setSuccess(`Report generated successfully! Report ID: ${report.report_id}`)
      
      // Automatically download the report
      try {
        const response = await historyAPI.downloadReport(report.report_id)
        const blob = new Blob([response.data], { 
          type: reportType === 'pdf' ? 'application/pdf' : 'application/json' 
        })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', report.report_name)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
        setSuccess(`Report "${report.report_name}" generated and downloaded successfully!`)
      } catch (downloadErr) {
        setSuccess(`Report generated! You can download it from the History page.`)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Report generation failed')
    } finally {
      setIsReportLoading(false)
    }
  }

  const isLargeFile = fileData && fileData.rows_count > 100000

  return (
    <div className="min-h-screen bg-black text-white p-4">
      <div className="max-w-7xl mx-auto">
        <div className="bg-gray-900 border border-gray-700 rounded-lg overflow-hidden">
          {/* Header */}
          <div className="bg-white text-black px-8 py-6 border-b border-gray-700">
            <h1 className="text-3xl font-bold">Survey Analysis</h1>
            <p className="text-gray-600 mt-2">Upload CSV files and analyze survey data</p>
          </div>

          {/* Content */}
          <div className="p-8">
            {error && (
              <div className="mb-6 bg-gray-800 border-l-4 border-red-500 text-white p-4 rounded-lg flex items-start gap-3 animate-slide-in">
                <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="flex-1">
                  <p className="text-sm font-medium">{error}</p>
                  <button
                    onClick={() => setError('')}
                    className="mt-2 text-xs text-gray-400 hover:text-white underline"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            )}

            {success && (
              <div className="mb-6 bg-gray-800 border-l-4 border-green-500 text-white p-4 rounded-lg flex items-start gap-3 animate-slide-in">
                <svg className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="flex-1">
                  <p className="text-sm font-medium">{success}</p>
                  <button
                    onClick={() => setSuccess('')}
                    className="mt-2 text-xs text-gray-400 hover:text-white underline"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            )}

            {/* Tabs */}
            <div className="flex space-x-4 mb-6 border-b border-gray-700">
              <button
                onClick={() => setActiveTab('upload')}
                className={`px-4 py-2 font-medium transition-colors ${
                  activeTab === 'upload'
                    ? 'border-b-2 border-white text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                Upload
              </button>
              <button
                onClick={() => setActiveTab('analysis')}
                className={`px-4 py-2 font-medium transition-colors ${
                  activeTab === 'analysis'
                    ? 'border-b-2 border-white text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
                disabled={!fileData}
              >
                Analysis
              </button>
            </div>

            {/* Upload Tab */}
            {activeTab === 'upload' && (
              <div className="space-y-6">
                <div className="border-2 border-dashed border-gray-700 rounded-lg p-8 text-center hover:border-gray-600 transition-colors">
                  <input
                    type="file"
                    accept=".csv"
                    onChange={handleFileUpload}
                    disabled={isLoading}
                    className="hidden"
                    id="file-upload"
                  />
                  <label
                    htmlFor="file-upload"
                    className="cursor-pointer flex flex-col items-center"
                  >
                    <svg
                      className="w-12 h-12 text-gray-500 mb-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                      />
                    </svg>
                    <span className="text-lg font-medium text-white">
                      {isLoading ? 'Uploading...' : 'Click to upload CSV file'}
                    </span>
                    <span className="text-sm text-gray-400 mt-2">
                      CSV files only • Supports files up to 1M+ rows
                    </span>
                  </label>
                </div>

                {fileData && (
                  <div className="bg-gray-800 border border-gray-600 rounded-lg p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-semibold text-white mb-3 text-lg">✓ File Uploaded Successfully</h3>
                        <div className="text-sm text-gray-300 space-y-2">
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <span className="text-gray-500">Filename:</span>
                              <p className="text-white font-medium">{fileData.filename}</p>
                            </div>
                            <div>
                              <span className="text-gray-500">Rows:</span>
                              <p className="text-white font-medium">{fileData.rows_count?.toLocaleString()}</p>
                            </div>
                            <div>
                              <span className="text-gray-500">Text Column:</span>
                              <p className="text-white font-medium">{fileData.text_col || 'Not detected'}</p>
                            </div>
                            <div>
                              <span className="text-gray-500">Time Column:</span>
                              <p className="text-white font-medium">{fileData.time_col || 'Not detected'}</p>
                            </div>
                          </div>
                          {isLargeFile && (
                            <div className="mt-3 p-3 bg-gray-700 rounded border border-gray-600">
                              <p className="text-yellow-400 text-sm">
                                ⚠ Large file detected. Use async processing for better performance.
                              </p>
                            </div>
                          )}
                          {fileData.issues && fileData.issues.length > 0 && (
                            <div className="mt-3">
                              <p className="font-semibold text-gray-400 mb-1">Issues:</p>
                              <ul className="list-disc list-inside text-gray-400">
                                {fileData.issues.map((issue, idx) => (
                                  <li key={idx}>{issue}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={() => setActiveTab('analysis')}
                        className="ml-4 btn-primary whitespace-nowrap"
                      >
                        Analyze →
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Analysis Tab */}
            {activeTab === 'analysis' && fileData && (
              <div className="space-y-6">
                <div className="flex items-center justify-between flex-wrap gap-4">
                  <h2 className="text-2xl font-bold text-white">Analysis Options</h2>
                  <div className="flex items-center gap-4">
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={useAI}
                        onChange={(e) => {
                          console.log('Use AI changed:', e.target.checked)
                          setUseAI(e.target.checked)
                        }}
                        className="w-4 h-4 bg-gray-800 border-gray-600 rounded focus:ring-white text-white"
                      />
                      <span className="text-sm text-gray-300">Use AI (OpenAI)</span>
                      <span className="text-xs text-gray-500 ml-1">(Requires API key)</span>
                    </label>
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={useLDA}
                        onChange={(e) => {
                          console.log('Use LDA changed:', e.target.checked)
                          setUseLDA(e.target.checked)
                        }}
                        className="w-4 h-4 bg-gray-800 border-gray-600 rounded focus:ring-white text-white"
                      />
                      <span className="text-sm text-gray-300">LDA Topic Modeling</span>
                      <span className="text-xs text-gray-500 ml-1">(Min 10 texts)</span>
                    </label>
                  </div>
                </div>

                {/* Date Range Filter */}
                {fileData.time_col && (
                  <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                    <h3 className="text-sm font-semibold text-gray-300 mb-3">Date Range Filter (Optional)</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm text-gray-400 mb-2">Start Date</label>
                        <input
                          type="date"
                          value={dateStart}
                          onChange={(e) => setDateStart(e.target.value)}
                          className="input-field"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-400 mb-2">End Date</label>
                        <input
                          type="date"
                          value={dateEnd}
                          onChange={(e) => setDateEnd(e.target.value)}
                          className="input-field"
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Report Generation Section */}
                <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white">Generate Report</h3>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleGenerateReport('pdf')}
                        disabled={isReportLoading || isLoading}
                        className="btn-primary flex items-center gap-2"
                      >
                        {isReportLoading ? (
                          <>
                            <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Generating...
                          </>
                        ) : (
                          <>
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Generate PDF Report
                          </>
                        )}
                      </button>
                      <button
                        onClick={() => handleGenerateReport('json')}
                        disabled={isReportLoading || isLoading}
                        className="btn-secondary flex items-center gap-2"
                      >
                        {isReportLoading ? (
                          <>
                            <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Generating...
                          </>
                        ) : (
                          <>
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                            </svg>
                            Generate JSON
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                  <p className="text-sm text-gray-400">
                    Generate a comprehensive report including sentiment analysis, themes, summaries, priorities, and trends.
                    Reports are automatically saved to your history.
                  </p>
                </div>

                {/* Analysis Buttons */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
                  <button
                    onClick={() => handleAnalyzeSentiment(false)}
                    disabled={isLoading || asyncTaskId}
                    className={`flex items-center justify-center gap-2 ${
                      activeAnalysis === 'sentiment' 
                        ? 'btn-primary' 
                        : 'btn-secondary'
                    }`}
                  >
                    {isLoading && activeAnalysis === 'sentiment' && !asyncTaskId ? (
                      <>
                        <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                        </svg>
                        Analyze Sentiment
                      </>
                    )}
                  </button>

                  {isLargeFile && (
                    <button
                      onClick={() => handleAnalyzeSentiment(true)}
                      disabled={isLoading || asyncTaskId}
                      className="btn-secondary flex items-center justify-center gap-2"
                    >
                      {asyncTaskId ? (
                        <>
                          <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Processing...
                        </>
                      ) : (
                        <>
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                          Async Analysis
                        </>
                      )}
                    </button>
                  )}

                  <button
                    onClick={handleExtractThemes}
                    disabled={isLoading || asyncTaskId}
                    className={`flex items-center justify-center gap-2 ${
                      activeAnalysis === 'themes' 
                        ? 'btn-primary' 
                        : 'btn-secondary'
                    }`}
                  >
                    {isLoading && activeAnalysis === 'themes' ? (
                      <>
                        <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Extracting...
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                        </svg>
                        Extract Themes
                      </>
                    )}
                  </button>

                  <button
                    onClick={handleGenerateSummaries}
                    disabled={isLoading || asyncTaskId}
                    className={`flex items-center justify-center gap-2 ${
                      activeAnalysis === 'summaries' 
                        ? 'btn-primary' 
                        : 'btn-secondary'
                    }`}
                  >
                    {isLoading && activeAnalysis === 'summaries' ? (
                      <>
                        <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Generating...
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        Generate Summaries
                      </>
                    )}
                  </button>

                  <button
                    onClick={(e) => {
                      e.preventDefault()
                      console.log('Trends button clicked', { isLoading, asyncTaskId, fileData: !!fileData })
                      handleAnalyzeTrends()
                    }}
                    disabled={isLoading || asyncTaskId || !fileData}
                    className={`flex items-center justify-center gap-2 ${
                      activeAnalysis === 'trends' 
                        ? 'btn-primary' 
                        : 'btn-secondary'
                    } ${(!fileData) ? 'opacity-50 cursor-not-allowed' : ''}`}
                    title={!fileData ? 'Please upload a file first' : ''}
                  >
                    {isLoading && activeAnalysis === 'trends' ? (
                      <>
                        <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                        </svg>
                        Analyze Trends
                      </>
                    )}
                  </button>

                  <button
                    onClick={handleGenerateWordCloud}
                    disabled={isLoading || asyncTaskId}
                    className={`flex items-center justify-center gap-2 ${
                      activeAnalysis === 'wordcloud' 
                        ? 'btn-primary' 
                        : 'btn-secondary'
                    }`}
                  >
                    {isLoading && activeAnalysis === 'wordcloud' ? (
                      <>
                        <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Generating...
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        Generate Word Cloud
                      </>
                    )}
                  </button>
                </div>

                {/* Semantic Search */}
                <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    <h3 className="text-lg font-semibold text-white">Semantic Search</h3>
                  </div>
                  <p className="text-xs text-gray-400 mb-3">Find similar responses using AI-powered semantic search</p>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && !isLoading && handleSemanticSearch()}
                      placeholder="e.g., 'app crashes frequently' or 'slow loading times'..."
                      className="flex-1 input-field"
                    />
                    <button
                      onClick={handleSemanticSearch}
                      disabled={isLoading || !searchQuery.trim()}
                      className={`whitespace-nowrap flex items-center gap-2 ${
                        activeAnalysis === 'semantic-search' 
                          ? 'btn-primary' 
                          : 'btn-secondary'
                      }`}
                    >
                      {isLoading && activeAnalysis === 'semantic-search' ? (
                        <>
                          <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Searching...
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                          </svg>
                          Search
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* Async Progress */}
                {asyncTaskId && asyncStatus && (
                  <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-lg font-semibold text-white">Processing in Background</h3>
                      <span className="text-sm text-gray-400">{asyncProgress}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2 mb-2">
                      <div
                        className="bg-white h-2 rounded-full transition-all duration-300"
                        style={{ width: `${asyncProgress}%` }}
                      ></div>
                    </div>
                    <p className="text-sm text-gray-400">{asyncStatus.message || 'Processing...'}</p>
                  </div>
                )}

                {/* Sentiment Results */}
                {isLoading && activeAnalysis === 'sentiment' && !sentimentData && <LoadingSkeleton type="chart" />}
                {sentimentData && activeAnalysis === 'sentiment' && (
                  <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-xl font-bold text-white">Sentiment Analysis Results</h3>
                      {sentimentData.processed_data && (
                        <span className="text-sm text-gray-400">
                          {sentimentData.processed_data.total_rows?.toLocaleString()} responses
                        </span>
                      )}
                    </div>
                    
                    {/* Quick Stats */}
                    <div className="grid grid-cols-3 gap-4 mb-6">
                      <div className="text-center p-4 bg-gray-900 rounded-lg border border-gray-700">
                        <div className="text-3xl font-bold text-white mb-1">
                          {sentimentData.sentiment_distribution?.positive || 0}
                        </div>
                        <div className="text-sm text-gray-400">Positive</div>
                      </div>
                      <div className="text-center p-4 bg-gray-900 rounded-lg border border-gray-700">
                        <div className="text-3xl font-bold text-white mb-1">
                          {sentimentData.sentiment_distribution?.neutral || 0}
                        </div>
                        <div className="text-sm text-gray-400">Neutral</div>
                      </div>
                      <div className="text-center p-4 bg-gray-900 rounded-lg border border-gray-700">
                        <div className="text-3xl font-bold text-white mb-1">
                          {sentimentData.sentiment_distribution?.negative || 0}
                        </div>
                        <div className="text-sm text-gray-400">Negative</div>
                      </div>
                    </div>

                    {/* Visualizations */}
                    <div className="pt-4 border-t border-gray-700">
                      <SentimentChart sentimentData={sentimentData} />
                    </div>

                    {/* Sentiment Over Time */}
                    {(sentimentData.sentiment_over_time || sentimentData.trend_metrics) && (
                      <div className="pt-6 border-t border-gray-700">
                        <h4 className="font-semibold text-white mb-4">Sentiment Trends Over Time</h4>
                        <SentimentTemporalChart 
                          sentimentOverTime={sentimentData.sentiment_over_time}
                          trendMetrics={sentimentData.trend_metrics}
                          currentFrequency={sentimentFrequency}
                          onFrequencyChange={async (freq) => {
                            // Update frequency and re-run analysis
                            setSentimentFrequency(freq)
                            setIsLoading(true)
                            setError('')
                            setSuccess('')
                            
                            try {
                              const response = await analysisAPI.sentiment(
                                fileData.file_id,
                                useAI,
                                dateStart || null,
                                dateEnd || null,
                                freq
                              )
                              setSentimentData(response)
                              setSuccess(`Sentiment analysis updated with ${freq === 'D' ? 'Daily' : freq === 'M' ? 'Monthly' : 'Weekly'} frequency!`)
                            } catch (err) {
                              console.error('Error updating sentiment with new frequency:', err)
                              setError(err.response?.data?.detail || 'Failed to update analysis with new frequency')
                            } finally {
                              setIsLoading(false)
                            }
                          }}
                        />
                      </div>
                    )}
                  </div>
                )}

                {/* Themes Results */}
                {isLoading && activeAnalysis === 'themes' && !themesData && <LoadingSkeleton type="card" />}
                {themesData && activeAnalysis === 'themes' && (
                  <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                    <h3 className="text-xl font-bold text-white mb-4">Themes & Priorities</h3>
                    
                    {/* Themes Section */}
                    {themesData.themes && themesData.themes.length > 0 && (
                      <div className="mb-6">
                        <h4 className="font-semibold text-white mb-3">Top Themes ({themesData.themes.length}):</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                          {themesData.themes.slice(0, 12).map((theme, idx) => (
                            <div key={idx} className="bg-gray-900 border border-gray-700 rounded-lg p-3 hover:border-gray-600 transition-colors">
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-white font-medium text-sm truncate flex-1">{theme.keyphrase || theme.name}</span>
                                {theme.weight && (
                                  <span className="text-xs text-gray-400 ml-2 whitespace-nowrap">{(theme.weight * 100).toFixed(1)}%</span>
                                )}
                              </div>
                              {theme.frequency && (
                                <p className="text-xs text-gray-500 mb-2">Frequency: {theme.frequency}</p>
                              )}
                              {theme.weight && (
                                <div className="w-full bg-gray-800 rounded-full h-1.5">
                                  <div
                                    className="bg-white h-1.5 rounded-full transition-all duration-300"
                                    style={{ width: `${Math.min(theme.weight * 100, 100)}%` }}
                                  />
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Theme Sentiment Section */}
                    {themesData.theme_sentiment && themesData.theme_sentiment.length > 0 && (
                      <div className="pt-6 border-t border-gray-700">
                        <h4 className="font-semibold text-white mb-4">Theme Sentiment Analysis</h4>
                        <ThemeSentimentChart themeSentiment={themesData.theme_sentiment} />
                      </div>
                    )}

                    {/* Theme Temporal Trends Section */}
                    {(themesData.theme_temporal || themesData.overall_trends) && (
                      <div className="pt-6 border-t border-gray-700">
                        <h4 className="font-semibold text-white mb-4">Theme Trends Over Time</h4>
                        <ThemeTemporalChart 
                          themeTemporal={themesData.theme_temporal} 
                          overallTrends={themesData.overall_trends}
                        />
                      </div>
                    )}

                    {/* Priorities Section with Chart */}
                    {themesData.priorities && themesData.priorities.length > 0 && (
                      <div className="pt-6 border-t border-gray-700">
                        <h4 className="font-semibold text-white mb-4">Priority Analysis ({themesData.priorities.length} themes):</h4>
                        <ThemePriorityChart priorities={themesData.priorities} />
                      </div>
                    )}
                  </div>
                )}

                {/* Trends Results */}
                {isLoading && activeAnalysis === 'trends' && !trendsData && <LoadingSkeleton type="card" />}
                {trendsData && activeAnalysis === 'trends' && (
                  <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-xl font-bold text-white">Trends Analysis</h3>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-400">Frequency:</span>
                        <select
                          value={trendsFrequency}
                          onChange={(e) => {
                            const newFreq = e.target.value
                            setTrendsFrequency(newFreq)
                            // Trigger re-analysis with new frequency
                            handleAnalyzeTrends(newFreq)
                          }}
                          className="bg-gray-900 border border-gray-700 text-white text-sm rounded px-2 py-1 cursor-pointer hover:bg-gray-700 transition-colors"
                        >
                          <option value="W">Weekly</option>
                          <option value="D">Daily</option>
                          <option value="M">Monthly</option>
                        </select>
                      </div>
                    </div>

                    {trendsData.summary && trendsData.summary.error ? (
                      <div className="bg-gray-900 border border-yellow-700 rounded-lg p-4">
                        <p className="text-yellow-400 text-sm">{trendsData.summary.error}</p>
                      </div>
                    ) : (
                      <>
                        {/* Summary Statistics */}
                        {trendsData.summary && (
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                            <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
                              <div className="text-sm text-gray-400 mb-1">Total Periods</div>
                              <div className="text-2xl font-bold text-white">{trendsData.summary.total_periods || 0}</div>
                            </div>
                            <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
                              <div className="text-sm text-gray-400 mb-1">Latest Sentiment</div>
                              <div className={`text-2xl font-bold ${
                                (trendsData.summary.latest_sentiment_index || 0) > 0.1 
                                  ? 'text-green-400' 
                                  : (trendsData.summary.latest_sentiment_index || 0) < -0.1 
                                  ? 'text-red-400' 
                                  : 'text-gray-400'
                              }`}>
                                {((trendsData.summary.latest_sentiment_index || 0) * 100).toFixed(1)}%
                              </div>
                            </div>
                            <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
                              <div className="text-sm text-gray-400 mb-1">Trend Direction</div>
                              <div className={`text-2xl font-bold ${
                                trendsData.summary.trend_direction === 'improving' 
                                  ? 'text-green-400' 
                                  : trendsData.summary.trend_direction === 'declining' 
                                  ? 'text-red-400' 
                                  : 'text-gray-400'
                              }`}>
                                {trendsData.summary.trend_direction === 'improving' ? '↑' : trendsData.summary.trend_direction === 'declining' ? '↓' : '→'}
                              </div>
                              <div className="text-xs text-gray-500 mt-1 capitalize">{trendsData.summary.trend_direction}</div>
                            </div>
                            <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
                              <div className="text-sm text-gray-400 mb-1">Sentiment Change</div>
                              <div className={`text-2xl font-bold ${
                                (trendsData.summary.sentiment_change || 0) > 0 
                                  ? 'text-green-400' 
                                  : (trendsData.summary.sentiment_change || 0) < 0 
                                  ? 'text-red-400' 
                                  : 'text-gray-400'
                              }`}>
                                {((trendsData.summary.sentiment_change || 0) * 100).toFixed(1)}%
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Trends Chart */}
                        {trendsData.trends && trendsData.trends.length > 0 && (
                          <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
                            <h4 className="font-semibold text-white mb-4">Trend Metrics Over Time</h4>
                            <SentimentTemporalChart 
                              sentimentOverTime={null}
                              trendMetrics={trendsData.trends}
                              currentFrequency={trendsData.frequency || 'W'}
                              onFrequencyChange={(freq) => {
                                setTrendsFrequency(freq)
                                handleAnalyzeTrends(freq)
                              }}
                            />
                          </div>
                        )}
                      </>
                    )}
                  </div>
                )}

                {/* Summaries Results */}
                {isLoading && activeAnalysis === 'summaries' && !summariesData && <LoadingSkeleton type="card" />}
                {summariesData && activeAnalysis === 'summaries' && (
                  <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 space-y-6">
                    <h3 className="text-xl font-bold text-white mb-4">Multi-Level Summaries</h3>
                    
                    {/* Executive Summary */}
                    {summariesData.executive_summary && (
                      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
                        <h4 className="font-semibold text-white mb-3">Executive Summary</h4>
                        <div className="text-sm text-gray-300 whitespace-pre-line">
                          {summariesData.executive_summary}
                        </div>
                      </div>
                    )}

                    {/* Overall Summary */}
                    {summariesData.overall && (
                      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
                        <h4 className="font-semibold text-white mb-3">Overall Summary</h4>
                        <p className="text-sm text-gray-300">{summariesData.overall}</p>
                      </div>
                    )}

                    {/* By Theme Summaries */}
                    {summariesData.by_theme && Object.keys(summariesData.by_theme).length > 0 && (
                      <div>
                        <h4 className="font-semibold text-white mb-3">Summaries by Theme</h4>
                        <div className="space-y-3">
                          {Object.entries(summariesData.by_theme).map(([theme, summary]) => (
                            <div key={theme} className="bg-gray-900 border border-gray-700 rounded-lg p-4">
                              <h5 className="font-medium text-white mb-2">{theme}</h5>
                              <p className="text-sm text-gray-300">{summary}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* By Segment Summaries */}
                    {summariesData.by_segment && Object.keys(summariesData.by_segment).length > 0 && (
                      <div>
                        <h4 className="font-semibold text-white mb-3">Summaries by Segment</h4>
                        <div className="space-y-3">
                          {Object.entries(summariesData.by_segment).map(([segment, summary]) => (
                            <div key={segment} className="bg-gray-900 border border-gray-700 rounded-lg p-4">
                              <h5 className="font-medium text-white mb-2">{segment}</h5>
                              <p className="text-sm text-gray-300">{summary}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Statistics */}
                    {summariesData.statistics && (
                      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
                        <h4 className="font-semibold text-white mb-3">Statistics</h4>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-gray-400">Total Responses:</span>
                            <span className="text-white font-medium ml-2">
                              {summariesData.statistics.total_responses?.toLocaleString()}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-400">Themes Analyzed:</span>
                            <span className="text-white font-medium ml-2">
                              {summariesData.statistics.themes_analyzed}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Word Cloud Results */}
                {isLoading && activeAnalysis === 'wordcloud' && !wordcloudData && <LoadingSkeleton type="card" />}
                {wordcloudData && activeAnalysis === 'wordcloud' && (
                  <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-xl font-bold text-white">Word Cloud</h3>
                      {wordcloudData.sentiment_distribution && (
                        <div className="flex gap-4 text-sm">
                          <span className="text-gray-400">
                            Positive: <span className="text-white font-medium">{wordcloudData.sentiment_distribution.positive || 0}</span>
                          </span>
                          <span className="text-gray-400">
                            Neutral: <span className="text-white font-medium">{wordcloudData.sentiment_distribution.neutral || 0}</span>
                          </span>
                          <span className="text-gray-400">
                            Negative: <span className="text-white font-medium">{wordcloudData.sentiment_distribution.negative || 0}</span>
                          </span>
                        </div>
                      )}
                    </div>
                    
                    <WordCloud
                      wordcloudPath={wordcloudData.wordcloud_path}
                      title="Sentiment Word Cloud"
                      description="Word size = frequency × |sentiment|. Green = positive, Red = negative, Gray = neutral"
                      className=""
                    />
                  </div>
                )}

                {/* Semantic Search Results */}
                {isLoading && activeAnalysis === 'semantic-search' && !semanticSearchData && <LoadingSkeleton type="card" />}
                {semanticSearchData && activeAnalysis === 'semantic-search' && (
                  <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                    <h3 className="text-xl font-bold text-white mb-4">
                      Similar Responses to: "{semanticSearchData.query_text}"
                    </h3>
                    <p className="text-sm text-gray-400 mb-4">
                      Found {semanticSearchData.total_found} similar responses
                    </p>
                    {semanticSearchData.results && semanticSearchData.results.length > 0 ? (
                      <div className="space-y-3">
                        {semanticSearchData.results.map((result, idx) => (
                          <div key={idx} className="bg-gray-900 border border-gray-700 rounded-lg p-4">
                            <div className="flex items-start justify-between mb-2">
                              <p className="text-sm text-gray-300 flex-1">{result.text}</p>
                              <span className="text-xs text-gray-500 ml-4 whitespace-nowrap">
                                {(result.score * 100).toFixed(1)}% similar
                              </span>
                            </div>
                            {result.metadata && Object.keys(result.metadata).length > 0 && (
                              <div className="mt-2 flex gap-2 flex-wrap">
                                {Object.entries(result.metadata).map(([key, value]) => (
                                  <span
                                    key={key}
                                    className="text-xs px-2 py-1 bg-gray-800 rounded text-gray-400"
                                  >
                                    {key}: {value}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-gray-400 text-sm">No similar responses found</p>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default SurveyAnalysis

