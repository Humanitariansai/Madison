import React, { useState } from 'react';
import { FileSidebar } from './FileSidebar';
import { ViolationSidebar } from './ViolationSidebar';
import { PDFComplianceViewer } from './PDFComplianceViewer';
import { Project, UploadedFile } from '../types';
import { ArrowLeft } from 'lucide-react';
import { Button } from './ui/Button';

interface Props {
  project: Project;
  onBack: () => void;
}

export const ProjectInspectionView: React.FC<Props> = ({ project, onBack }) => {
  // We can manage file selection state locally here
  // Default to the first file in the project
  const [activeFileId, setActiveFileId] = useState<string | null>(project.files[0]?.id || null);
  const [selectedViolationId, setSelectedViolationId] = useState<string | null>(null);

  const activeFile = project.files.find(f => f.id === activeFileId);

  return (
    <div className="flex h-screen w-full bg-white overflow-hidden font-sans">
      {/* 1. Left Sidebar: Navigation */}
      <div className="flex flex-col h-full">
        {/* Back Button Area */}
        <div className="w-72 shrink-0 bg-slate-950 text-white border-b border-slate-800 p-4">
            <button
                onClick={onBack}
                className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors text-sm font-medium"
            >
                <ArrowLeft size={16} /> Back to Dashboard
            </button>
        </div>

        {/* Reusing existing FileSidebar but mapping project files */}
        <div className="flex-1 min-h-0 w-full">
            <FileSidebar
                files={project.files}
                activeFileId={activeFileId}
                onSelectFile={setActiveFileId}
                onUploadClick={() => alert("Add file to project feature coming soon!")}
            />
        </div>
      </div>

      {/* 2. Center Stage: PDF Viewer */}
      <div className="flex-1 relative h-full min-w-0 flex flex-col">
        {/* Project Header Bar */}
        <div className="h-14 bg-white border-b flex items-center px-6 justify-between shrink-0 z-20">
            <div className="flex items-center gap-4">
                <h2 className="font-semibold text-slate-800">{project.title}</h2>
                <span className="text-slate-300">|</span>
                <span className="text-sm text-slate-500">Brand Kit: {project.brandKit.title}</span>
            </div>
            <div className="text-sm font-bold text-primary">
                Score: {project.score}%
            </div>
        </div>

        <div className="flex-1 relative min-h-0">
            <PDFComplianceViewer
            pdfUrl={activeFile?.url || null}
            violations={activeFile?.violations || []}
            selectedViolationId={selectedViolationId}
            onSelectViolation={setSelectedViolationId}
            />
        </div>
      </div>

      {/* 3. Right Sidebar: Inspector */}
      {activeFile && (
        <ViolationSidebar
          violations={activeFile.violations}
          selectedId={selectedViolationId}
          onSelect={setSelectedViolationId}
        />
      )}
    </div>
  );
};
