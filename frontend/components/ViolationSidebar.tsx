import React from 'react';
import { InspectionResult, InspectionLevel } from '../types';
import { AlertTriangle, AlertCircle, Info, CheckCircle } from 'lucide-react';

interface Props {
  violations: InspectionResult[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

const LevelIcon: React.FC<{ level: InspectionLevel }> = ({ level }) => {
  switch (level) {
    case 'CRITICAL': return <AlertCircle size={16} className="text-red-600" />;
    case 'MEDIUM': return <AlertTriangle size={16} className="text-amber-500" />;
    case 'LOW': return <Info size={16} className="text-blue-500" />;
    case 'PASS': return <CheckCircle size={16} className="text-green-600" />;
    default: return <Info size={16} className="text-gray-500" />;
  }
};

const LevelBadge: React.FC<{ level: InspectionLevel }> = ({ level }) => {
  const colors = {
    'CRITICAL': 'bg-red-100 text-red-700 border-red-200',
    'MEDIUM': 'bg-amber-100 text-amber-800 border-amber-200',
    'LOW': 'bg-blue-100 text-blue-700 border-blue-200',
    'PASS': 'bg-green-100 text-green-700 border-green-200',
  };

  return (
    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${colors[level]}`}>
      {level}
    </span>
  );
};

export const ViolationSidebar: React.FC<Props> = ({ violations, selectedId, onSelect }) => {
  // Sort: Critical -> Medium -> Low -> Pass
  const sortedViolations = [...violations].sort((a, b) => {
    const weights = { CRITICAL: 4, MEDIUM: 3, LOW: 2, PASS: 1 };
    return weights[b.level] - weights[a.level];
  });

  // Filter out pass items if we want to show only issues? 
  // User asked to see ALL bounding boxes. But maybe sidebar should focus on issues?
  // Let's show all for now as per "view all properties" request, but maybe grouped?
  // User said "I want to be able to view all the tagged bounding boxes with filler text violation based on pass or fail."
  // So we show all.

  const issueCount = violations.filter(v => v.status === 'FAIL').length;

  if (violations.length === 0) {
    return (
      <div className="w-96 shrink-0 bg-white border-l h-full flex flex-col items-center justify-center text-center p-6 text-gray-500">
        <CheckCircle size={48} className="text-green-500 mb-4" />
        <h3 className="font-bold text-gray-800 mb-1">No Items Found</h3>
        <p className="text-sm">No inspection data available for this document.</p>
      </div>
    );
  }

  return (
    <div className="w-96 shrink-0 bg-white border-l h-full flex flex-col shadow-xl z-20">
      <div className="p-4 border-b bg-gray-50">
        <h2 className="font-bold text-gray-900 flex items-center gap-2">
          {issueCount > 0 ? <AlertCircle className="text-red-500" size={20} /> : <CheckCircle className="text-green-500" size={20} />}
          Inspection Report
        </h2>
        <p className="text-xs text-gray-500 mt-1">
            Found {violations.length} items ({issueCount} issues)
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {sortedViolations.map((v) => (
          <div
            key={v.id}
            onClick={() => onSelect(v.id)}
            className={`
              group mb-3 p-4 rounded-lg border cursor-pointer transition-all duration-200 relative
              ${selectedId === v.id
                ? 'bg-primary/5 border-primary/30 ring-1 ring-primary/30 shadow-md transform scale-[1.02]'
                : 'bg-white border-gray-200 hover:border-gray-300 hover:shadow-sm'
              }
            `}
          >
            <div className="flex justify-between items-start mb-2">
              <div className="flex items-center gap-2">
                <LevelIcon level={v.level} />
                <span className="text-xs font-bold text-gray-500 tracking-wider">PAGE {v.pageNumber}</span>
              </div>
              <LevelBadge level={v.level} />
            </div>

            <p className={`text-sm font-medium mb-1 ${selectedId === v.id ? 'text-primary' : 'text-gray-800'}`}>
              {v.message}
            </p>

            <p className="text-xs text-gray-400 font-mono mt-2">
              Type: {v.type}
            </p>

            {/* Selection Indicator */}
            {selectedId === v.id && (
              <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary rounded-l-lg" />
            )}
          </div>
        ))}
      </div>

      <div className="p-4 border-t bg-gray-50 text-xs text-center text-gray-400">
        Brand Guide AI Automated Inspection v1.0
      </div>
    </div>
  );
};
