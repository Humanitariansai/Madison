import React from 'react';
import { UploadedFile } from '../types';
import { FileText, Plus, ChevronRight, ShieldCheck, Clock } from 'lucide-react';
import { Button } from './ui/Button';

interface Props {
  files: UploadedFile[];
  activeFileId: string | null;
  onSelectFile: (id: string) => void;
  onUploadClick: () => void;
}

export const FileSidebar: React.FC<Props> = ({
  files,
  activeFileId,
  onSelectFile,
  onUploadClick
}) => {
  return (
    <div className="w-72 shrink-0 bg-slate-900 text-slate-300 flex flex-col h-full border-r border-slate-800">
      <div className="p-4 border-b border-slate-800">
        <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
            Project Files
        </h3>
        {/* We can re-enable this button later for multi-file projects */}
        {/*
        <Button
            variant="secondary"
            className="w-full text-xs"
            onClick={onUploadClick}
        >
          <Plus size={14} /> Add Asset
        </Button>
        */}
      </div>

      <div className="flex-1 overflow-y-auto py-2">
        {files.length === 0 ? (
            <div className="px-5 text-slate-500 text-sm italic py-4">
                No files in this project.
            </div>
        ) : (
            <ul className="space-y-1">
            {files.map((file) => (
                <li key={file.id}>
                <button
                    onClick={() => onSelectFile(file.id)}
                    className={`w-full flex items-center gap-3 px-5 py-3 transition-colors text-left border-l-2
                    ${activeFileId === file.id
                        ? 'bg-slate-800 border-primary text-white'
                        : 'border-transparent text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                    }`}
                >
                    <FileText size={18} className={activeFileId === file.id ? 'text-primary' : 'text-slate-600'} />
                    <div className="flex-1 overflow-hidden">
                        <p className="text-sm font-medium truncate">{file.name}</p>
                        <p className="text-[10px] text-slate-500 flex items-center gap-1 mt-0.5">
                            <Clock size={10} />
                            {new Date(file.uploadDate).toLocaleDateString()}
                        </p>
                    </div>
                    {activeFileId === file.id && <ChevronRight size={14} className="text-primary" />}
                </button>
                </li>
            ))}
            </ul>
        )}
      </div>

      <div className="p-4 border-t border-slate-800">
        <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center font-bold text-xs text-white">
                JD
            </div>
            <div>
                <p className="text-sm font-medium text-white">John Doe</p>
                <p className="text-xs text-slate-500">Design Lead</p>
            </div>
        </div>
      </div>
    </div>
  );
};
