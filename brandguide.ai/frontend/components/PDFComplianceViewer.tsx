import React, { useState, useEffect, useRef } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { InspectionResult } from '../types';
import { AlertCircle, ZoomIn, ZoomOut, Maximize } from 'lucide-react';

// Configure PDF worker
// react-pdf v10 uses pdfjs-dist v4, which requires the .mjs worker
pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface Props {
  pdfUrl: string | null;
  violations: InspectionResult[];
  selectedViolationId: string | null;
  onSelectViolation: (id: string) => void;
}

export const PDFComplianceViewer: React.FC<Props> = ({
  pdfUrl,
  violations,
  selectedViolationId,
  onSelectViolation
}) => {
  const [numPages, setNumPages] = useState<number>(0);
  // ... (rest of state items are fine)
  const [scale, setScale] = useState<number>(1.2);
  const [errorInfo, setErrorInfo] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const violationRefs = useRef<{[key: string]: HTMLDivElement | null}>({});

  // Auto-scroll to selected violation
  useEffect(() => {
    if (selectedViolationId && violationRefs.current[selectedViolationId]) {
      violationRefs.current[selectedViolationId]?.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      });
    }
  }, [selectedViolationId]);

  if (!pdfUrl) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-gray-400 bg-gray-50">
        <AlertCircle size={48} className="mb-4 opacity-50" />
        <p className="text-lg font-medium">No document selected</p>
        <p className="text-sm">Select a file from the sidebar to inspect</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-100">
      {/* Toolbar */}
      <div className="bg-white border-b px-6 py-3 flex items-center justify-between shadow-sm z-10 sticky top-0">
        <div className="text-sm font-medium text-gray-600">
          Viewing Mode: <span className="text-primary">Inspection</span>
        </div>
        <div className="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setScale(s => Math.max(0.5, s - 0.1))}
            className="p-1.5 hover:bg-white rounded-md transition-colors text-gray-600"
            title="Zoom Out"
          >
            <ZoomOut size={18} />
          </button>
          <span className="text-xs font-medium min-w-[3rem] text-center">{Math.round(scale * 100)}%</span>
          <button
            onClick={() => setScale(s => Math.min(3, s + 0.1))}
            className="p-1.5 hover:bg-white rounded-md transition-colors text-gray-600"
            title="Zoom In"
          >
            <ZoomIn size={18} />
          </button>
        </div>
        <div className="flex items-center gap-2">
            <button
                onClick={() => setScale(1.0)}
                className="text-xs font-medium text-gray-500 hover:text-primary px-2"
            >
                Reset Zoom
            </button>
        </div>
      </div>

      {/* PDF Container */}
      <div
        className="flex-1 overflow-auto p-8 relative"
        ref={containerRef}
      >
        <Document
          file={pdfUrl}
          className="flex flex-col gap-8 w-fit mx-auto"
          onLoadSuccess={({ numPages }) => {
            setNumPages(numPages);
            setErrorInfo(null);
          }}
          onLoadError={(err) => {
            console.error('PDF Load Error:', err);
            setErrorInfo(err.message);
          }}
          loading={
            <div className="flex items-center justify-center h-96">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            </div>
          }
          error={
            <div className="flex flex-col items-center justify-center h-96 text-red-500">
                <AlertCircle size={32} className="mb-2"/>
                <p className="font-medium">Failed to load PDF</p>
                {errorInfo && (
                  <p className="text-xs mt-2 text-red-600 bg-red-50 p-2 rounded max-w-xs text-center font-mono break-all">
                    {errorInfo}
                  </p>
                )}
            </div>
          }
        >
          {Array.from(new Array(numPages), (_, index) => {
            const pageNumber = index + 1;
            const pageViolations = violations.filter(v => v.pageNumber === pageNumber);

            return (
              <div
                key={`page_${pageNumber}`}
                className="relative shadow-xl bg-white"
              >
                <Page
                  pageNumber={pageNumber}
                  scale={scale}
                  renderTextLayer={false}
                  renderAnnotationLayer={false}
                  className="bg-white"
                />

                {/* Violation Overlays */}
                <div className="absolute inset-0 pointer-events-none">
                  {pageViolations.map((v) => {
                    const isActive = selectedViolationId === v.id;
                    const isPass = v.status === 'PASS';

                    return (
                      <div
                        key={v.id}
                        ref={el => {
                            if (el) violationRefs.current[v.id] = el;
                        }}
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectViolation(v.id);
                        }}
                        className={`
                          absolute border-2 cursor-pointer pointer-events-auto transition-all duration-200
                          ${isActive
                            ? 'ring-4 z-20 ' + (isPass ? 'ring-green-400 border-green-600' : 'ring-red-400 border-red-600')
                            : 'z-10 ' + (isPass ? 'border-green-500 bg-green-500/10 hover:bg-green-500/20' : 'border-red-500 bg-red-500/10 hover:bg-red-500/20')
                          }
                        `}
                        style={{
                          left: `${v.coordinates.x * 100}%`,
                          top: `${v.coordinates.y * 100}%`,
                          width: `${v.coordinates.width * 100}%`,
                          height: `${v.coordinates.height * 100}%`,
                        }}
                      >
                         {/* Badge for ID */}
                        <div
                            className={`
                                absolute -top-3 -right-3 w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold text-white shadow-sm
                                ${isPass ? 'bg-green-600' : 'bg-red-600'}
                                ${isActive ? 'scale-110' : ''}
                            `}
                        >
                            {isPass ? '✓' : '!'}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </Document>
      </div>
    </div>
  );
};
