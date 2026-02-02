import React, { useState } from 'react';
import { X } from 'lucide-react';
import { Button } from "./ui/button"
import { Input } from "./ui/input";
import { Spinner } from './ui/spinner';
import { FileUploader } from './FileUploader';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: { name: string; files: File[] }) => void;
  isProcessing: boolean;
}

export const CreateBrandKitDialog: React.FC<Props> = ({ isOpen, onClose, onSubmit, isProcessing }) => {
  const [name, setName] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

  if (!isOpen) return null;

  const handleSubmit = () => {
    if (selectedFiles.length > 0 && name) {
      onSubmit({ name, files: selectedFiles });
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-xl overflow-hidden flex flex-col max-h-[90vh]">

        {/* Header */}
        <div className="p-6 border-b flex justify-between items-center bg-slate-50">
          <div>
            <h2 className="text-xl font-bold text-slate-900">Create New Brand Kit</h2>
            <p className="text-sm text-slate-500">Setup a new brand guideline.</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-slate-200 rounded-full transition-colors">
            <X size={20} className="text-slate-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 flex-1 overflow-y-auto">
          {isProcessing ? (
            <div className="flex flex-col items-center justify-center h-64 text-center">
              <Spinner size={48} className="text-primary mb-6" />
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Analyzing Documents...</h3>
              <p className="text-slate-500 max-w-sm">
                Extracting colors, fonts, and logos from <strong>{selectedFiles.length}</strong> file(s).
              </p>
            </div>
          ) : (
            <>
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">Guidelines Name</label>
                <Input
                  placeholder="e.g., Q4 Corporate Guidelines"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  autoFocus
                />
              </div>

              <FileUploader
                label="Upload Assets"
                files={selectedFiles}
                onFilesChange={setSelectedFiles}
                multiple={true}
                accept="application/pdf, .otf, .ttf"
                helperText="Upload PDF guides, Logo sheets, or Typography docs."
              />
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-slate-50 flex justify-end gap-3">
          <Button variant="ghost" onClick={onClose} disabled={isProcessing}>Cancel</Button>
          <Button
            disabled={selectedFiles.length === 0 || !name || isProcessing}
            onClick={handleSubmit}
          >
            {isProcessing && <Spinner className="mr-2 h-4 w-4" />}
            Create Guidelines ({selectedFiles.length})
          </Button>
        </div>
      </div>
    </div>
  );
};
