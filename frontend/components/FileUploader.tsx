import React, { useState, useCallback } from 'react';
import { Upload, FileText, X, FileType, Trash2 } from 'lucide-react';

interface FileUploaderProps {
  label?: string;
  accept?: string;
  files: File[]; // CHANGED: Now accepts an array
  onFilesChange: (files: File[]) => void; // CHANGED: Returns array
  multiple?: boolean; // NEW: Toggle multi-upload
  helperText?: string;
}

export const FileUploader: React.FC<FileUploaderProps> = ({
  label = "Upload File",
  accept = "application/pdf",
  files,
  onFilesChange,
  multiple = false,
  helperText
}) => {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleFiles = useCallback((newFiles: File[]) => {
    if (multiple) {
      // Filter duplicates based on name
      const existingNames = new Set(files.map(f => f.name));
      const uniqueFiles = newFiles.filter(f => !existingNames.has(f.name));
      onFilesChange([...files, ...uniqueFiles]);
    } else {
      // Single mode: just take the first one
      if (newFiles.length > 0) onFilesChange([newFiles[0]]);
    }
  }, [files, multiple, onFilesChange]);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files?.length) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.length) {
      handleFiles(Array.from(e.target.files));
    }
    e.target.value = ''; // Reset input
  };

  const removeFile = (nameToRemove: string) => {
    onFilesChange(files.filter(f => f.name !== nameToRemove));
  };

  return (
    <div className="space-y-3">
      <label className="text-sm font-medium text-slate-700">{label}</label>

      {/* Drop Zone */}
      <div
        className={`
          border-2 border-dashed rounded-lg p-6 text-center transition-all cursor-pointer relative
          ${isDragOver ? 'border-primary bg-primary/5' : 'border-slate-300 hover:border-slate-400 hover:bg-slate-50'}
          ${files.length > 0 ? 'bg-slate-50' : ''}
        `}
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => document.getElementById('hidden-file-input')?.click()}
      >
        <input
          type="file"
          id="hidden-file-input"
          className="hidden"
          accept={accept}
          multiple={multiple} // Enforce HTML behavior
          onChange={handleChange}
        />

        <div className="flex flex-col items-center">
            <div className="w-10 h-10 bg-white border border-slate-200 rounded-full flex items-center justify-center mb-3 text-slate-400 shadow-sm">
                <Upload size={18} />
            </div>
            <p className="text-sm font-medium text-slate-700">
                {multiple ? "Drag files here or click to upload" : "Click to upload file"}
            </p>
            <p className="text-xs text-slate-500 mt-1">
                {helperText || (multiple ? "Multiple files allowed" : "Single file only")}
            </p>
        </div>
      </div>

      {/* Selected Files List */}
      {files.length > 0 && (
        <div className="space-y-2 max-h-40 overflow-y-auto pr-1 custom-scrollbar">
            {files.map((file) => (
                <div key={file.name} className="flex items-center justify-between p-3 bg-white border border-slate-200 rounded-lg shadow-sm group">
                    <div className="flex items-center gap-3 overflow-hidden">
                        <div className="p-2 bg-primary/10 rounded-md shrink-0">
                            <FileText className="text-primary" size={18} />
                        </div>
                        <div className="text-left overflow-hidden">
                            <p className="font-medium text-sm text-slate-900 truncate">{file.name}</p>
                            <p className="text-xs text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                        </div>
                    </div>
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            removeFile(file.name);
                        }}
                        className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-md transition-colors"
                    >
                        <Trash2 size={16} />
                    </button>
                </div>
            ))}
        </div>
      )}
    </div>
  );
};
