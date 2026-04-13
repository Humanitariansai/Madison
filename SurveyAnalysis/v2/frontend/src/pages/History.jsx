import { useState, useEffect } from 'react'
import { historyAPI } from '../services/api'
import api from '../services/api'
import LoadingSkeleton from '../components/LoadingSkeleton'

const History = () => {
  const [files, setFiles] = useState([])
  const [reports, setReports] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('files')

  useEffect(() => {
    loadHistory()
  }, [])

  const loadHistory = async () => {
    setIsLoading(true)
    setError('')
    try {
      const [filesData, reportsData] = await Promise.all([
        historyAPI.getFiles(),
        historyAPI.getReports()
      ])
      setFiles(filesData)
      setReports(reportsData)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load history')
    } finally {
      setIsLoading(false)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    const date = new Date(dateString)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatFileSize = (bytes) => {
    if (!bytes) return 'N/A'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const handleDownloadReport = async (reportId, reportName) => {
    try {
      const response = await historyAPI.downloadReport(reportId)
      
      // Create blob and download
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', reportName)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setError('Failed to download report')
    }
  }

  return (
    <div className="min-h-screen bg-black p-4">
      <div className="max-w-7xl mx-auto">
        <div className="bg-gray-900 border border-gray-700 rounded-lg overflow-hidden">
          {/* Header */}
          <div className="bg-white text-black px-8 py-6 border-b border-gray-700">
            <h1 className="text-3xl font-bold">History</h1>
            <p className="text-gray-600 mt-2">View your uploaded files and generated reports</p>
          </div>

          {/* Content */}
          <div className="p-8">
            {error && (
              <div className="mb-6 bg-gray-800 border-l-4 border-red-500 text-white p-4 rounded-lg flex items-start gap-3">
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

            {/* Tabs */}
            <div className="flex space-x-4 mb-6 border-b border-gray-700">
              <button
                onClick={() => setActiveTab('files')}
                className={`px-4 py-2 font-medium transition-colors ${
                  activeTab === 'files'
                    ? 'border-b-2 border-white text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                Uploaded Files ({files.length})
              </button>
              <button
                onClick={() => setActiveTab('reports')}
                className={`px-4 py-2 font-medium transition-colors ${
                  activeTab === 'reports'
                    ? 'border-b-2 border-white text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                Generated Reports ({reports.length})
              </button>
            </div>

            {isLoading ? (
              <div className="space-y-4">
                <LoadingSkeleton type="table" />
                <LoadingSkeleton type="table" />
                <LoadingSkeleton type="table" />
              </div>
            ) : (
              <>
                {/* Files Tab */}
                {activeTab === 'files' && (
                  <div className="space-y-4">
                    {files.length === 0 ? (
                      <div className="text-center py-12 bg-gray-800 rounded-lg border border-gray-700">
                        <svg
                          className="mx-auto h-12 w-12 text-gray-600"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                          />
                        </svg>
                        <h3 className="mt-2 text-sm font-medium text-white">No files uploaded</h3>
                        <p className="mt-1 text-sm text-gray-400">Get started by uploading a CSV file.</p>
                      </div>
                    ) : (
                      files.map((file) => (
                        <div
                          key={file.id}
                          className="border border-gray-700 rounded-lg p-6 bg-gray-800 hover:border-gray-600 transition-colors"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center space-x-3 mb-2">
                                <svg
                                  className="h-8 w-8 text-white"
                                  fill="none"
                                  stroke="currentColor"
                                  viewBox="0 0 24 24"
                                >
                                  <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                                  />
                                </svg>
                                <div>
                                  <h3 className="text-lg font-semibold text-white">{file.filename}</h3>
                                  <p className="text-sm text-gray-400">Uploaded {formatDate(file.uploaded_at)}</p>
                                </div>
                              </div>

                              <div className="grid grid-cols-3 gap-4 mt-4">
                                <div>
                                  <p className="text-xs text-gray-500">Rows</p>
                                  <p className="text-sm font-semibold text-white">{file.rows_count?.toLocaleString() || 'N/A'}</p>
                                </div>
                                <div>
                                  <p className="text-xs text-gray-500">File Hash</p>
                                  <p className="text-sm font-mono text-gray-400">{file.file_hash?.substring(0, 8)}...</p>
                                </div>
                                <div>
                                  <p className="text-xs text-gray-500">Reports</p>
                                  <p className="text-sm font-semibold text-white">{file.reports?.length || 0}</p>
                                </div>
                              </div>

                              {/* Reports for this file */}
                              {file.reports && file.reports.length > 0 && (
                                <div className="mt-4 pt-4 border-t border-gray-700">
                                  <h4 className="text-sm font-semibold text-gray-300 mb-2">Generated Reports:</h4>
                                  <div className="space-y-2">
                                    {file.reports.map((report) => (
                                      <div
                                        key={report.id}
                                        className="flex items-center justify-between bg-gray-900 rounded-lg p-3 border border-gray-700"
                                      >
                                        <div className="flex-1">
                                          <p className="text-sm font-medium text-white">{report.report_name}</p>
                                          <div className="flex items-center space-x-4 mt-1">
                                            <span className="text-xs text-gray-500 uppercase">
                                              {report.report_type}
                                            </span>
                                            <span className="text-xs text-gray-500">
                                              {formatFileSize(report.file_size)}
                                            </span>
                                            <span className="text-xs text-gray-500">
                                              {formatDate(report.generated_at)}
                                            </span>
                                            {report.date_range_start && report.date_range_end && (
                                              <span className="text-xs text-gray-500">
                                                {formatDate(report.date_range_start)} - {formatDate(report.date_range_end)}
                                              </span>
                                            )}
                                          </div>
                                        </div>
                                        <button
                                          onClick={() => handleDownloadReport(report.id, report.report_name)}
                                          className="ml-4 px-4 py-2 bg-white text-black text-sm font-medium rounded-lg hover:bg-gray-200 transition-colors"
                                        >
                                          Download
                                        </button>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}

                {/* Reports Tab */}
                {activeTab === 'reports' && (
                  <div className="space-y-4">
                    {reports.length === 0 ? (
                      <div className="text-center py-12 bg-gray-800 rounded-lg border border-gray-700">
                        <svg
                          className="mx-auto h-12 w-12 text-gray-600"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                          />
                        </svg>
                        <h3 className="mt-2 text-sm font-medium text-white">No reports generated</h3>
                        <p className="mt-1 text-sm text-gray-400">Generate reports from your uploaded files.</p>
                      </div>
                    ) : (
                      reports.map((report) => (
                        <div
                          key={report.id}
                          className="border border-gray-700 rounded-lg p-6 bg-gray-800 hover:border-gray-600 transition-colors"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center space-x-3 mb-2">
                                <svg
                                  className="h-8 w-8 text-white"
                                  fill="none"
                                  stroke="currentColor"
                                  viewBox="0 0 24 24"
                                >
                                  <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                                  />
                                </svg>
                                <div>
                                  <h3 className="text-lg font-semibold text-white">{report.report_name}</h3>
                                  <p className="text-sm text-gray-400">Generated {formatDate(report.generated_at)}</p>
                                </div>
                              </div>

                              <div className="grid grid-cols-4 gap-4 mt-4">
                                <div>
                                  <p className="text-xs text-gray-500">Type</p>
                                  <p className="text-sm font-semibold text-white uppercase">{report.report_type}</p>
                                </div>
                                <div>
                                  <p className="text-xs text-gray-500">Size</p>
                                  <p className="text-sm font-semibold text-white">{formatFileSize(report.file_size)}</p>
                                </div>
                                {report.date_range_start && report.date_range_end && (
                                  <>
                                    <div>
                                      <p className="text-xs text-gray-500">Start Date</p>
                                      <p className="text-sm font-semibold text-white">
                                        {formatDate(report.date_range_start)}
                                      </p>
                                    </div>
                                    <div>
                                      <p className="text-xs text-gray-500">End Date</p>
                                      <p className="text-sm font-semibold text-white">
                                        {formatDate(report.date_range_end)}
                                      </p>
                                    </div>
                                  </>
                                )}
                              </div>

                              {report.file_info && (
                                <div className="mt-4 pt-4 border-t border-gray-700">
                                  <p className="text-xs text-gray-500 mb-1">Source File</p>
                                  <p className="text-sm font-medium text-white">{report.file_info.filename}</p>
                                  <p className="text-xs text-gray-500 mt-1">
                                    Uploaded {formatDate(report.file_info.uploaded_at)}
                                  </p>
                                </div>
                              )}
                            </div>

                            <button
                              onClick={() => handleDownloadReport(report.id, report.report_name)}
                              className="ml-4 px-6 py-3 bg-white text-black font-medium rounded-lg hover:bg-gray-200 transition-colors"
                            >
                              Download
                            </button>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default History
