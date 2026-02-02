import { useState, useEffect } from 'react';
import { Dashboard } from './components/Dashboard';
import { ProjectInspectionView } from './components/ProjectInspectionView';
import { CreateProjectDialog } from './components/CreateProjectDialog';
import { BrandKit, Project, ApiBrandKitResponse, ApiProjectResponse } from './types';
import { CreateBrandKitDialog } from './components/CreateBrandKitDialog';
import { BrandKitInspectionView } from './components/BrandKitInspectionView';
import { API_BASE } from './lib/api';
import { mapApiBrandKitToFrontend, mapApiProjectToFrontend } from './lib/mappers';

// Layout Imports
import { SidebarProvider, SidebarInset, SidebarTrigger } from '@/components/ui/sidebar';
import { AppSidebar } from '@/components/AppSidebar';
import { Separator } from '@/components/ui/separator';
import { Breadcrumb, BreadcrumbItem, BreadcrumbList, BreadcrumbPage, BreadcrumbLink, BreadcrumbSeparator } from '@/components/ui/breadcrumb';
import { Button } from '@/components/ui/button';
import { Bell, Edit2, Upload, MoreVertical } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export default function App() {
  const [view, setView] = useState<'dashboard' | 'projectInspection' | 'brandKitInspection'>('dashboard');
  const [activeTab, setActiveTab] = useState<'dashboard' | 'projects' | 'kits' | 'settings'>('dashboard');

  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);

  const [isProjectCreateDialogOpen, setIsProjectCreateDialogOpen] = useState(false);
  const [isBrandKitCreateDialogOpen, setIsBrandKitCreateDialogOpen] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const [activeBrandKitId, setActiveBrandKitId] = useState<string | null>(null);
  const [brandKits, setBrandKits] = useState<BrandKit[]>([]);
  const [changeView, setChangeView] = useState<boolean>(true);

  // Initialize data on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [bkRes, projRes] = await Promise.all([
          fetch(`${API_BASE}/brandkits`),
          fetch(`${API_BASE}/projects?expand=brandKit`)
        ]);

        if (bkRes.ok) {
          const bks: ApiBrandKitResponse[] = await bkRes.json();
          const mappedBrandKits = bks.map(data => mapApiBrandKitToFrontend(data, API_BASE));
          setBrandKits(mappedBrandKits);
        }

        if (projRes.ok) {
          const projs: ApiProjectResponse[] = await projRes.json();
          const mappedProjects = projs.map(p => mapApiProjectToFrontend(p, API_BASE));

          setProjects(mappedProjects);
        }
      } catch (e) {
        console.error("Failed to fetch initial data:", e);
      }
    };
    fetchData();
  }, []);

  const handleCreateProject = async ({ name, brandKit, file }: { name: string, brandKit: BrandKit, file: File }) => {
    setIsProcessing(true);

    try {
      const formData = new FormData();
      const projectId = crypto.randomUUID();

      formData.append('id', projectId);
      formData.append('title', name);
      formData.append('brand_kit_id', brandKit.id);
      formData.append('file', file);

      const response = await fetch(`${API_BASE}/project/audit`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Audit failed');
      }

      const data: ApiProjectResponse = await response.json();
      console.log("Audit Response Data:", data);

      const newProject = mapApiProjectToFrontend(data, API_BASE);

      setProjects(prev => [newProject, ...prev]);
      setIsProjectCreateDialogOpen(false);
      setActiveProjectId(newProject.id);
      setView('projectInspection');
      setActiveTab('projects');

    } catch (error) {
      console.error('Failed to audit project:', error);
      alert(`Audit failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleOpenProject = (id: string) => {
    setActiveProjectId(id);
    setView('projectInspection');
    setActiveTab('projects');
  };

  const activeProject = projects.find(p => p.id === activeProjectId);

  const handleCreateBrandKit = async ({ name, files }: { name: string, files: File[] }) => {
    setIsProcessing(true);

    try {
      const formData = new FormData();
      const brandKitId = crypto.randomUUID();

      formData.append('id', brandKitId);
      formData.append('title', name);

      // Append each file with the same field name
      files.forEach((file) => {
        formData.append('files', file);
      });

      const response = await fetch(`${API_BASE}/brandkit`, {
        method: 'POST',
        body: formData,
        // Don't set Content-Type header - browser sets it with boundary
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const apiResponse: ApiBrandKitResponse = data;
      const newBrandKit = mapApiBrandKitToFrontend(apiResponse, API_BASE);

      setBrandKits(prev => [newBrandKit, ...prev]);
      setIsBrandKitCreateDialogOpen(false);

      if (changeView) {
        setActiveBrandKitId(newBrandKit.id);
        setView('brandKitInspection');
        setActiveTab('kits');
      }
      setChangeView(true);

    } catch (error) {
      console.error('Failed to create brand kit:', error);
      alert('Failed to create brand kit. Is the backend running?');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleOpenBrandKit = (id: string) => {
    console.log("Opening brandkit with id:", id)
    setActiveBrandKitId(id);
    setView('brandKitInspection');
    setActiveTab('kits');
  };

  const activeBrandKit = brandKits.find(b => b.id === activeBrandKitId);

  // Helper to get sidebar active tab based on current view
  const currentSidebarTab = view === 'projectInspection' ? 'projects' :
    view === 'brandKitInspection' ? 'kits' : activeTab;

  // Tab titles for dashboard
  const tabTitles = {
    dashboard: 'Dashboard',
    projects: 'Projects',
    kits: 'Brand Kits',
    settings: 'Settings'
  };

  return (
    <SidebarProvider className="h-screen overflow-hidden">
      <AppSidebar
        activeTab={currentSidebarTab}
        setActiveTab={(tab) => {
          setActiveTab(tab);
          setView('dashboard'); // Always go back to dashboard/list view when clicking sidebar nav
        }}
        projects={projects}
        brandKits={brandKits}
      />
      <SidebarInset className="flex flex-col overflow-hidden">
        {/* Global Header inside Inset */}
        <header className="flex h-16 shrink-0 items-center gap-2 px-4 transition-[width,height] ease-linear group-has-[[data-collapsible=icon]]/sidebar-wrapper:h-12">
          <div className="flex items-center gap-2">
            <SidebarTrigger className="-ml-1" />
            <Separator orientation="vertical" className="mr-2 h-4" />
            <Breadcrumb>
              <BreadcrumbList>
                {view === 'dashboard' && (
                  <BreadcrumbItem>
                    <BreadcrumbPage className="capitalize font-semibold text-lg">{tabTitles[activeTab]}</BreadcrumbPage>
                  </BreadcrumbItem>
                )}

                {view === 'projectInspection' && activeProject && (
                  <>
                    <BreadcrumbItem>
                      <BreadcrumbLink
                        className="cursor-pointer hover:text-foreground transition-colors"
                        onClick={() => {
                          setView('dashboard');
                          setActiveTab('projects');
                        }}
                      >
                        Projects
                      </BreadcrumbLink>
                    </BreadcrumbItem>
                    <BreadcrumbSeparator />
                    <BreadcrumbItem>
                      <BreadcrumbPage className="font-medium">{activeProject.title}</BreadcrumbPage>
                    </BreadcrumbItem>
                  </>
                )}

                {view === 'brandKitInspection' && activeBrandKit && (
                  <>
                    <BreadcrumbItem>
                      <BreadcrumbLink
                        className="cursor-pointer hover:text-foreground transition-colors"
                        onClick={() => {
                          setView('dashboard');
                          setActiveTab('kits');
                        }}
                      >
                        Brand Kits
                      </BreadcrumbLink>
                    </BreadcrumbItem>
                    <BreadcrumbSeparator />
                    <BreadcrumbItem>
                      <BreadcrumbPage className="font-medium">{activeBrandKit.title}</BreadcrumbPage>
                    </BreadcrumbItem>
                    {view === 'brandKitInspection' && (
                      <Badge variant="outline" className="ml-2 text-primary border-primary/20 bg-primary/5 hidden sm:inline-flex">Active</Badge>
                    )}
                  </>
                )}
              </BreadcrumbList>
            </Breadcrumb>
          </div>

          <div className="ml-auto flex items-center gap-2">
            {view === 'brandKitInspection' ? (
              <>
                <Button variant="outline" size="sm" className="hidden sm:flex h-8 gap-1">
                  <Edit2 size={14} />
                  <span className="whitespace-nowrap">Edit Rules</span>
                </Button>
                <Button size="sm" className="hidden sm:flex h-8 gap-1">
                  <Upload size={14} />
                  <span className="whitespace-nowrap">Add Assets</span>
                </Button>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <MoreVertical size={16} />
                </Button>
              </>
            ) : (
              <Button variant="outline" size="icon" className="bg-background">
                <Bell size={16} />
              </Button>
            )}
          </div>
        </header>

        {/* Main Content Area with Inset and Rounded Borders */}
        <div className="flex flex-1 flex-col gap-4 p-4 pt-0 overflow-hidden">
          <div className="flex-1 rounded-xl bg-muted/50 border overflow-hidden flex flex-col min-h-0 shadow-sm">
            {view === 'dashboard' && (
              <Dashboard
                activeTab={activeTab} // Use the lifted state
                projects={projects}
                onCreateProject={() => {
                  console.log("Triggered onCreateProject")
                  setIsProjectCreateDialogOpen(true)
                }}
                onOpenProject={handleOpenProject}
                brandKits={brandKits}
                onCreateBrandKit={() => {
                  console.log("Triggered onCreateBrandKit")
                  setIsBrandKitCreateDialogOpen(true)
                }}
                onOpenBrandKit={handleOpenBrandKit}
              />
            )}

            {view === 'projectInspection' && activeProject && (
              <ProjectInspectionView
                project={activeProject}
                onBack={() => {
                  setView('dashboard');
                  setActiveTab('projects');
                }}
              />
            )}

            {view === 'brandKitInspection' && activeBrandKit && (
              <BrandKitInspectionView
                brandKit={activeBrandKit}
                onBack={() => {
                  setView('dashboard');
                  setActiveTab('kits');
                }}
              />
            )}
          </div>
        </div>
      </SidebarInset>

      <CreateProjectDialog
        isOpen={isProjectCreateDialogOpen}
        onCreateBrandKit={() => {
          console.log("Triggered onCreateProject")
          setIsBrandKitCreateDialogOpen(true)
          setChangeView(false)
        }}
        onClose={() => setIsProjectCreateDialogOpen(false)}
        onSubmit={handleCreateProject}
        isProcessing={isProcessing}
        brandKits={brandKits}
      />
      <CreateBrandKitDialog
        isOpen={isBrandKitCreateDialogOpen}
        onClose={() => setIsBrandKitCreateDialogOpen(false)}
        onSubmit={handleCreateBrandKit}
        isProcessing={isProcessing}
      />
    </SidebarProvider>
  );
}
