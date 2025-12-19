import React, { useState } from 'react';
import { X } from 'lucide-react';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { Spinner } from './ui/Spinner';
import { FileUploader } from './FileUploader';
import { BrandKit } from '@/types';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  // NOTE: Returns a single 'file', not an array
  onSubmit: ({ name, brandKit, file }: { name: string; brandKit: BrandKit; file: File }) => void;
  isProcessing: boolean;
  brandKits: BrandKit[];
  onCreateBrandKit: () => void;
}

export const CreateProjectDialog: React.FC<Props> = ({ isOpen, onClose, onSubmit, isProcessing, brandKits, onCreateBrandKit }) => {
  const DEFAULT_OPTION = "Create new brand kit"
  const [name, setName] = useState('');
  const [brandKit, setBrandKit] = useState<string>(brandKits?.at(0)?.title ?? DEFAULT_OPTION);

  // STATE: Single file only
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  if (!isOpen) return null;

  const handleSubmit = () => {
    if (selectedFile && name) {
      const selectedBrandKit = brandKits.find((kit) => kit.title === brandKit);
      if (selectedBrandKit) {
        onSubmit({ name, brandKit: selectedBrandKit, file: selectedFile });
      }
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-xl overflow-hidden flex flex-col max-h-[90vh]">

        {/* Header */}
        <div className="p-6 border-b flex justify-between items-center bg-slate-50">
          <div>
            <h2 className="text-xl font-bold text-slate-900">Create New Project</h2>
            <p className="text-sm text-slate-500">Setup a new brand compliance inspection.</p>
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
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Analyzing Document...</h3>
              <p className="text-slate-500 max-w-sm">
                Scanning <strong>{selectedFile?.name}</strong> against <strong>{brandKit}</strong>...
              </p>
            </div>
          ) : (
            <>
              {/* 1. Project Name */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">Project Name</label>
                <Input
                  placeholder="e.g., Q3 Financial Report 2024"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  autoFocus
                />
              </div>

              {/* 2. Brand Kit Selection */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">Brand Guidelines</label>
                <select
                  className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm focus:ring-2 focus:ring-primary outline-none"
                  value={brandKit}
                  onChange={(e) => setBrandKit(e.target.value)}
                >
                  {brandKits.map((kit) => <option key={kit.id} value={kit.title}>{kit.title}</option>)}
                  <option value={DEFAULT_OPTION}>+ Create new brand kit</option>
                </select>
              </div>

              {/* 3. File Uploader (Single Mode) */}
              <FileUploader
                label="Upload Asset"
                // Adapter: Convert single state to array for the component
                files={selectedFile ? [selectedFile] : []}
                // Adapter: Extract first item from array to set single state
                onFilesChange={(files) => setSelectedFile(files[0] ?? null)}
                multiple={false}
                accept=".pdf,application/pdf"
                helperText="Upload a single PDF to verify."
              />
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-slate-50 flex justify-end gap-3">
          <Button variant="ghost" onClick={onClose} disabled={isProcessing}>Cancel</Button>

          {brandKit === DEFAULT_OPTION ? (
            <Button onClick={onCreateBrandKit}>
              Create Brand Kit &rarr;
            </Button>
          ) : (
            <Button
              disabled={!selectedFile || !name || isProcessing}
              onClick={handleSubmit}
              isLoading={isProcessing}
            >
              Create Project
            </Button>
          )}
        </div>
      </div>
    </div >
  );
};
