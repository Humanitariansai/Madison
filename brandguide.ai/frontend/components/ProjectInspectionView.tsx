import React, { useState } from 'react';
import { ViolationSidebar } from './ViolationSidebar';
import { PDFComplianceViewer } from './PDFComplianceViewer';
import { Project } from '../types';
import { Button } from "@/components/ui/button";
import { PanelRightClose, PanelRightOpen, GripVertical } from 'lucide-react';
import { cn } from "@/lib/utils";

interface Props {
  project: Project;
  onBack: () => void;
}

export const ProjectInspectionView: React.FC<Props> = ({ project }) => {
  // Default to the first file in the project since we only support single file per project now
  const [activeFileId, setActiveFileId] = useState<string | null>(project.files[0]?.id || null);
  const [selectedViolationId, setSelectedViolationId] = useState<string | null>(null);
  const [isInspectorOpen, setIsInspectorOpen] = useState(true);

  const activeFile = project.files.find(f => f.id === activeFileId);

  return (
    <div className="flex h-full w-full bg-background overflow-hidden font-sans border-t group/project-view">
      {/* 1. Center Stage: PDF Viewer */}
      <div className="flex-1 relative h-full min-w-0 flex flex-col bg-muted/5 transition-all duration-300 ease-in-out">
        {/* Project Context Sub-Header */}
        <div className="h-10 bg-background border-b flex items-center px-4 justify-between shrink-0 z-20 shadow-sm">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className="font-medium text-foreground">Audit Context:</span>
            <span className="bg-muted px-2 py-0.5 rounded font-mono text-[10px]">{project.brandKit?.title || 'Unknown Brand Kit'}</span>
            {activeFile && <span className="text-muted-foreground ml-2 hidden sm:inline-block">File: {activeFile.name}</span>}
          </div>

          <div className="flex items-center gap-4">
            <div className="text-xs font-bold text-primary flex items-center gap-1">
              Compliance Score:
              <span className="text-sm font-mono">{project.score}%</span>
            </div>

            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 ml-2 text-muted-foreground hover:text-foreground"
              onClick={() => setIsInspectorOpen(!isInspectorOpen)}
              title={isInspectorOpen ? "Close Inspector" : "Open Inspector"}
            >
              {isInspectorOpen ? <PanelRightClose size={14} /> : <PanelRightOpen size={14} />}
            </Button>
          </div>
        </div>

        <div className="flex-1 relative min-h-0 p-4">
          <div className="h-full w-full bg-background shadow-sm border rounded-lg overflow-hidden relative">
            <PDFComplianceViewer
              pdfUrl={activeFile?.url || null}
              violations={activeFile?.violations || []}
              selectedViolationId={selectedViolationId}
              onSelectViolation={setSelectedViolationId}
            />
          </div>
        </div>
      </div>

      {/* 2. Right Sidebar: Inspector */}
      <div
        className={cn(
          "border-l bg-background transition-[width] duration-300 ease-in-out overflow-hidden flex flex-col h-full shrink-0",
          isInspectorOpen ? "w-80 border-l" : "w-0 border-l-0"
        )}
      >
        <div className="w-80 h-full flex flex-col">
          {activeFile && (
            <ViolationSidebar
              violations={activeFile.violations}
              selectedId={selectedViolationId}
              onSelect={setSelectedViolationId}
            />
          )}
        </div>
      </div>
    </div>
  );
};
