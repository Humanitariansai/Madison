import React, { useState } from 'react';
import { Upload, X, FileCheck, ArrowRight, Trash2, FileText } from 'lucide-react';
import { Button } from './ui/Button';
import { Spinner } from './ui/Spinner';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (file: File[]) => void;
  isProcessing: boolean;
}

export const UploadModal: React.FC<Props> = ({ isOpen, onClose, onUpload, isProcessing }) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);

  if (!isOpen) return null;

  const handleNewFiles = (newFiles: File[]) => {
    const validPdfs = newFiles.filter(f => f.type === 'application/pdf')
    setSelectedFiles(prev => {
      const existingNames = new Set(prev.map(f => f.name))
      const uniqueNewFiles = validPdfs.filter(f => !existingNames.has(f.name))
      return [...prev, ...uniqueNewFiles]
    })
  }
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const filesToBeAdded = Array.from(e.dataTransfer.files)
      handleNewFiles(filesToBeAdded)
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const filesToBeAdded = e.target.files
    if (filesToBeAdded && filesToBeAdded.length > 0) {
      handleNewFiles(Array.from(filesToBeAdded))
    }
    e.target.value = ''
  };

  const removeFile = (fileName: string) => {
    setSelectedFiles(prev => prev.filter(f => f.name !== fileName))
  }

  const handleSubmit = () => {
    if (selectedFiles.length > 0) {
      onUpload(selectedFiles);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-6 border-b flex justify-between items-center bg-gray-50">
          <div>
            <h2 className="text-xl font-bold text-gray-800">New Compliance Inspection</h2>
            <p className="text-sm text-gray-500">Upload a PDF to scan for brand violations</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-200 rounded-full transition-colors">
            <X size={20} className="text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-8 flex-1 overflow-y-auto">
          {isProcessing ? (
            <div className="flex flex-col items-center justify-center h-64 text-center">
              <Spinner size={48} className="text-indigo-600 mb-6" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Analyzing Document...</h3>
              <p className="text-gray-500 max-w-sm">
                Our AI is scanning for fonts, colors, and logo misuse. This usually takes about 10-20 seconds.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Guidelines Status (Mock) */}
              <div className="flex items-center p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="bg-green-100 p-2 rounded-full mr-4">
                  <FileCheck size={24} className="text-green-600" />
                </div>
                <div>
                  <h4 className="font-semibold text-green-900">Brand Guidelines Active</h4>
                  <p className="text-sm text-green-700">Using "2024 Corporate Identity V2.pdf" as reference.</p>
                </div>
              </div>

              {/* Upload Area */}
              <div
                className={`
                        border-2 border-dashed rounded-xl p-10 text-center transition-all cursor-pointer
                        ${isDragOver ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'}
                        ${selectedFiles.length > 0 ? 'bg-indigo-50 border-indigo-200' : ''}
                    `}
                onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
                onDragLeave={() => setIsDragOver(false)}
                onDrop={handleDrop}
                onClick={() => document.getElementById('fileInput')?.click()}
              >
                <input
                  type="file"
                  id="fileInput"
                  className="hidden"
                  accept="application/pdf"
                  onChange={handleFileChange}
                />

                {selectedFiles.length > 0 ? (
                  <div className="flex flex-col gap-3">
                    <div className="text-sm text-gray-500 mb-2 font-medium">
                      {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''} selected. Click to add more.
                    </div>

                    {/* File List */}
                    <div className="max-h-48 overflow-y-auto space-y-2 px-2" onClick={e => e.stopPropagation()}>
                      {selectedFiles.map((file) => (
                        <div key={file.name} className="flex items-center justify-between p-3 bg-white border rounded-lg shadow-sm group">
                          <div className="flex items-center gap-3 overflow-hidden">
                            <div className="bg-indigo-100 p-2 rounded">
                              <FileText size={18} className="text-indigo-600" />
                            </div>
                            <div className="text-left">
                              <p className="text-sm font-medium text-gray-900 truncate max-w-[200px]">{file.name}</p>
                              <p className="text-xs text-gray-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                            </div>
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation(); // Stop click from opening file dialog
                              removeFile(file.name);
                            }}
                            className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center py-4">
                    <div className="w-16 h-16 bg-gray-100 text-gray-400 rounded-full flex items-center justify-center mb-4">
                      <Upload size={32} />
                    </div>
                    <h3 className="font-semibold text-gray-700 mb-1">Click to upload or drag and drop</h3>
                    <p className="text-sm text-gray-500">PDF files only (Multiple allowed)</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-gray-50 flex justify-end gap-3">
          <Button variant="ghost" onClick={onClose} disabled={isProcessing}>Cancel</Button>
          <Button
            disabled={selectedFiles.length === 0 || isProcessing}
            onClick={handleSubmit}
            className={isProcessing ? 'opacity-50' : ''}
          >
            {isProcessing ? 'Processing...' : (
              <>
                Start Inspection ({selectedFiles.length}) <ArrowRight size={16} />
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};
