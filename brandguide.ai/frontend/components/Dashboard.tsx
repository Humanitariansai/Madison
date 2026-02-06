import React, { useState } from 'react';
import { BrandKit, Project } from '../types';
import { DashboardView } from '@/components/DashboardView';
import { BrandKitView } from '@/components/BrandKitView';
import { ProjectsView } from '@/components/ProjectsView';

interface Props {
  activeTab: 'dashboard' | 'projects' | 'kits' | 'settings';
  projects: Project[];
  onOpenProject: (projectId: string) => void;
  onCreateProject: () => void;
  brandKits: BrandKit[];
  onOpenBrandKit: (brandKitId: string) => void;
  onCreateBrandKit: () => void;
}

export const Dashboard: React.FC<Props> = ({
  activeTab, // Now received as a prop
  projects,
  onOpenProject,
  onCreateProject,
  brandKits,
  onOpenBrandKit,
  onCreateBrandKit
}) => {
  // Removed internal state for activeTab
  // Removed internal tabTitles mapping (moved to App.tsx for breadcrumbs)

  const DisplayTab = ({ activeTab }: { activeTab: string }) => {
    if (activeTab === 'dashboard') {
      return <DashboardView
        projects={projects.slice(0, 5)} onCreateProject={onCreateProject}
        onOpenProject={onOpenProject}
      />
    }
    else if (activeTab === 'projects') {
      return <ProjectsView projects={projects} onCreateProject={onCreateProject} onOpenProject={onOpenProject} />
    }
    else if (activeTab === 'kits') {
      return <BrandKitView brandKits={brandKits} projects={projects} onCreateBrandKit={onCreateBrandKit} onOpenBrandKit={onOpenBrandKit} />
    }
    else {
      return <div className="p-8">Settings Placeholder</div>
    }
  }

  return (
    <main className="flex flex-1 flex-col gap-4 p-4 overflow-auto">
      <DisplayTab activeTab={activeTab} />
    </main>
  );
};
