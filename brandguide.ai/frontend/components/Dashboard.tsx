import React, { useState } from 'react';
import { BrandKit, Project } from '../types';
import {
  ShieldCheck,
  LayoutDashboard, FolderKanban, Palette, Settings, User,
  MoreVertical
} from 'lucide-react';
import { Avatar } from './ui/Avatar';
import { DashboardView } from './DashboardView';
import { BrandKitView } from './BrandKitView';

interface Props {
  projects: Project[];
  onOpenProject: (projectId: string) => void;
  onCreateProject: () => void;
  brandKits: BrandKit[];
  onOpenBrandKit: (brandKitId: string) => void;
  onCreateBrandKit: () => void;
}

export const Dashboard: React.FC<Props> = ({ projects, onOpenProject, onCreateProject, brandKits, onOpenBrandKit, onCreateBrandKit }) => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'projects' | 'kits' | 'settings'>('dashboard');
  const NavItem = ({
    id,
    icon: Icon,
    label,
    count
  }: {
    id: string,
    icon: React.ElementType,
    label: string,
    count?: number
  }) => (
    <button
      onClick={() => setActiveTab(id as any)}
      className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-colors mb-1
        ${activeTab === id
          ? 'bg-slate-900 text-white'
          : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
        }`}
    >
      <div className="flex items-center gap-3">
        <Icon size={18} />
        {label}
      </div>
      {count !== undefined && (
        <span className={`text-xs px-2 py-0.5 rounded-full ${activeTab === id ? 'bg-slate-700' : 'bg-slate-200'}`}>
          {count}
        </span>
      )}
    </button>
  );

  const DisplayTab = ({ activeTab }) => {
    console.log("activeTab", activeTab)
    if (activeTab === 'dashboard') {
      console.log("displaying dashboard")
      return <DashboardView
        projects={projects} onCreateProject={onCreateProject}
        onOpenProject={onOpenProject}
      />
    }
    else if (activeTab === 'projects') {
      return <></>
    }
    else if (activeTab === 'kits') {
      return <BrandKitView brandKits={brandKits} onCreateBrandKit={onCreateBrandKit} onOpenBrandKit={onOpenBrandKit} />
    }
    else {
      return <></>
    }
  }

  return (
    <div className="flex min-h-screen bg-slate-50 font-sans text-slate-900">

      {/* APP SIDEBAR */}
      <aside className="w-64 bg-white border-r border-slate-200 hidden md:flex flex-col fixed inset-y-0 z-50">
        {/* Brand Header */}
        <div className="p-6 flex items-center gap-2">
          <div className="bg-primary p-1.5 rounded-lg">
            <ShieldCheck className="text-white" size={20} />
          </div>
          <span className="font-bold text-lg tracking-tight">Brand Guide AI</span>
        </div>

        {/* Navigation */}
        <div className="flex-1 px-4 py-2 space-y-6 overflow-y-auto">
          <div>
            <p className="px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Platform</p>
            <NavItem id="dashboard" icon={LayoutDashboard} label="Dashboard" />
            <NavItem id="projects" icon={FolderKanban} label="Projects" count={projects.length} />
            <NavItem id="kits" icon={Palette} label="Brand Kits" count={brandKits.length}/>
          </div>

          <div>
            <p className="px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Configuration</p>
            <NavItem id="settings" icon={Settings} label="Settings" />
            <NavItem id="members" icon={User} label="Team Members" />
          </div>
        </div>

        {/* User Account View */}
        <div className="p-4 border-t border-slate-200">
          <button className="flex items-center gap-3 w-full p-2 rounded-lg hover:bg-slate-50 transition-colors group text-left">
            <Avatar fallback="JD" className="bg-primary/10 text-primary" />
            <div className="flex-1 overflow-hidden">
              <p className="text-sm font-medium text-slate-900 truncate">John Doe</p>
              <p className="text-xs text-slate-500 truncate">john@brandguide.ai</p>
            </div>
            <MoreVertical size={16} className="text-slate-400 group-hover:text-slate-600" />
          </button>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="flex-1 md:pl-64 flex flex-col min-w-0">
        <DisplayTab activeTab={activeTab} />
      </main>
    </div>
  );
};
