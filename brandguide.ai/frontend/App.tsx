import React, { useState } from 'react';
import { Dashboard } from './components/Dashboard';
import { ProjectInspectionView } from './components/ProjectInspectionView';
import { CreateProjectDialog } from './components/CreateProjectDialog';
import { BrandKit, Project, UploadedFile, InspectionResult } from './types';
import { CreateBrandKitDialog } from './components/CreateBrandKitDialog';
import { BrandKitInspectionView } from './components/BrandKitInspectionView';



export default function App() {
  const [view, setView] = useState<'dashboard' | 'ProjectInspection' | 'brandKitInspection'>('dashboard');
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);

  const [isProjectCreateDialogOpen, setIsProjectCreateDialogOpen] = useState(false);
  const [isBrandKitCreateDialogOpen, setIsBrandKitCreateDialogOpen] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const [activeBrandKitId, setActiveBrandKitId] = useState<string | null>(null);
  const [brandKits, setBrandKits] = useState<BrandKit[]>([]);
  const [changeView, setChangeView] = useState<boolean>(true);

  // Initialize data on mount
  React.useEffect(() => {
    const fetchData = async () => {
      try {
        const [bkRes, projRes] = await Promise.all([
          fetch('http://localhost:8000/brandkits'),
          fetch('http://localhost:8000/projects')
        ]);

        if (bkRes.ok) {
           const bks = await bkRes.json();
           // Map backend brand kits to frontend structure if needed
           // Backend returns full brand kit objects now from our new GET endpoint logic
           
           // Backend returns array of BrandKits. We need to ensure Logos/Files are mapped correctly relative to frontend interfaces?
           // The backend returns "assets" list. Frontend uses "files" and "logos".
           // We might need to map them here similar to how we do in handleCreateBrandKit.
           
           const API_BASE = "http://localhost:8000";
           const mappedBrandKits = bks.map((data: any) => {
             const uploadedFiles: UploadedFile[] = (data.assets || []).map((asset: any) => ({
                id: asset.id,
                name: asset.filename,
                url: asset.url ? `${API_BASE}${asset.url}` : '',
                status: 'ready',
                violations: [],
                uploadDate: data.date, 
             }));
             
             return {
               id: data.id,
               title: data.title,
               date: data.date,
               colors: data.colors || [],
               
               // Map Rich Data
               rich_colors: data.rich_colors || [],
               typography: data.typography || [],
               logo_rules: data.logo_rules || [],
               forbidden_keywords: data.forbidden_keywords || [],
               brand_voice_attributes: data.brand_voice_attributes || [],

               imagery: [],
               files: uploadedFiles,
               logos: (data.assets || [])
                 .filter((f: any) => f.category === "LOGO")
                 .map((f: any) => ({
                   id: f.id,
                   name: f.filename,
                   url: f.url ? `${API_BASE}${f.url}` : '',
                   variant: 'Primary'
                 }))
             }
           });
           
           setBrandKits(mappedBrandKits);
        }

        if (projRes.ok) {
           const projs = await projRes.json();
           // Map backend projects
           const API_BASE = "http://localhost:8000";
           const mappedProjects = projs.map((p: any) => {
             // We need to link the brandKit object.
             // This might be tricky if brandKits aren't set yet. 
             // Logic will rely on matching ID later or searching the fetched bks array.
             // Since we construct mappedBrandKits in this scope, let's use it.
             
             // Wait, we can't easily access mappedBrandKits here if we did parallel fetch? 
             // Actually we can chaining or just assume we have the ID to find it in rendering.
             // But Project interface requires `brandKit: BrandKit`.
             // We'll iterate bks.
             
             // Let's defer this map inside the `then` or `await` block.
             return {
                 id: p.id,
                 title: p.title,
                 date: p.date,
                 status: p.status,
                 score: p.score,
                 brandKit: null, // Placeholder, we'll fix below
                 brandKitId: p.brandKitId, // Temp field to help matching
                 files: (p.files || []).map((f: any) => ({
                    ...f,
                    url: f.url ? `${API_BASE}${f.url}` : ''
                 }))
             }
           });
           
           setProjects(mappedProjects);
        }
      } catch (e) {
        console.error("Failed to fetch initial data:", e);
      }
    };
    fetchData();
  }, []);
  
  // Effect to link projects to brand kits once both are loaded
  React.useEffect(() => {
    if (projects.length > 0 && brandKits.length > 0) {
        // If projects have null brandKit but valid brandKitId
        const updated = projects.map(p => {
             if (p.brandKit) return p; // Already linked
             // @ts-ignore - access temp field
             const bkId = p.brandKitId;
             if (bkId) {
                 const foundBk = brandKits.find(bk => bk.id === bkId);
                 if (foundBk) return { ...p, brandKit: foundBk };
             }
             return p;
        });
        
        // Only update if changes were made to avoid loops?
        // JSON.stringify comparison is heavy but safe for small data.
        // Or checking if any was null.
        if (projects.some(p => !p.brandKit && (p as any).brandKitId)) {
            setProjects(updated);
        }
    }
  }, [brandKits, projects.length]); // Re-run when lists change

  // Helper to generate mock violations for new uploads
  const generateMockViolations = (fileId: string): InspectionResult[] => {
    return [
      {
        id: `v_${fileId}_1`,
        pageNumber: 1,
        type: 'FONT',
        message: "Incorrect font family. Expected 'Inter', found 'Arial'.",
        level: 'CRITICAL',
        status: 'FAIL',
        coordinates: { x: 50, y: 100, width: 200, height: 40 }
      },
      {
        id: `v_${fileId}_2`,
        pageNumber: 1,
        type: 'LOGO',
        message: "Logo safety margin violated (15px < 20px).",
        level: 'MEDIUM',
        status: 'FAIL',
        coordinates: { x: 400, y: 50, width: 100, height: 80 }
      },
    ];
  };

  const handleCreateProject = async ({ name, brandKit, file }: { name: string, brandKit: BrandKit, file: File }) => {
    setIsProcessing(true);

    try {
      const formData = new FormData();
      const projectId = crypto.randomUUID();

      formData.append('id', projectId);
      formData.append('title', name);
      formData.append('brand_kit_id', brandKit.id);
      formData.append('file', file);

      const response = await fetch('http://localhost:8000/project/audit', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Audit failed');
      }

      const data = await response.json();
      console.log("Audit Response Data:", data); // Requested Debug Log

      const newFile: UploadedFile = {
        id: crypto.randomUUID(),
        name: file.name,
        url: URL.createObjectURL(file), // Only for preview
        status: 'ready',
        violations: data.violations, // Contains both PASS and FAIL results now
        uploadDate: new Date().toLocaleDateString()
      };

      const newProject: Project = {
        id: data.projectId,
        title: data.title,
        date: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
        status: data.status,
        score: data.score,
        brandKit: brandKit,
        files: [newFile]
      };

      setProjects(prev => [newProject, ...prev]);
      setIsProjectCreateDialogOpen(false);
      setActiveProjectId(newProject.id);
      setView('ProjectInspection');

    } catch (error) {
      console.error('Failed to audit project:', error);
      alert(`Audit failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleOpenProject = (id: string) => {
    // If opening a mock project with no files, let's inject a dummy file/alert for demo purposes
    // In a real app, we would fetch the project details
    const project = projects.find(p => p.id === id);
    if (project && project.files.length === 0) {
      // Just for demo continuity, add a mock file if empty
      alert("This demo project has no PDF attached. Please create a new project to see the viewer in action.");
      return;
    }
    setActiveProjectId(id);
    setView('ProjectInspection');
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

      const response = await fetch('http://localhost:8000/brandkit', {
        method: 'POST',
        body: formData,
        // Don't set Content-Type header - browser sets it with boundary
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

    const data = await response.json();
    // Response shape: { id, title, assets: [{ id, filename, category, path, url }] }

    // Map response to UploadedFiles with classification info
    // We use the backend URL for the files now
    const API_BASE = "http://localhost:8000";

    const newUploadedFiles: UploadedFile[] = data.assets.map((asset: any) => ({
      id: asset.id, // Use backend ID
      name: asset.filename,
      url: asset.url ? `${API_BASE}${asset.url}` : '', // Use backend served URL
      status: 'ready',
      violations: [],
      uploadDate: new Date().toLocaleDateString(),
    }));

    const newBrandKit: BrandKit = {
      id: data.id, // Use backend ID
      title: data.title,
      date: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
      colors: data.colors || [],
      
      // Map Rich Data
      rich_colors: data.rich_colors || [],
      typography: data.typography || [],
      logo_rules: data.logo_rules || [],
      forbidden_keywords: data.forbidden_keywords || [],
      brand_voice_attributes: data.brand_voice_attributes || [],

      imagery: [],
      files: newUploadedFiles,
      logos: data.assets
        .filter((f: any) => f.category === "LOGO")
        .map((f: any) => ({
          id: f.id,
          name: f.filename,
          url: f.url ? `${API_BASE}${f.url}` : '',
          variant: 'Primary' // Default
        }))
    };

    setBrandKits(prev => [newBrandKit, ...prev]);
    setIsBrandKitCreateDialogOpen(false);

    if (changeView) {
      setActiveBrandKitId(newBrandKit.id);
      setView('brandKitInspection');
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
    // If opening a mock project with no files, let's inject a dummy file/alert for demo purposes
    // In a real app, we would fetch the project details
    console.log("Opening brandkit with id:", id)
    const brandKit = brandKits.find(b => b.id === id);
    setActiveBrandKitId(id);
    setView('brandKitInspection');
  };

  const activeBrandKit = brandKits.find(b => b.id === activeBrandKitId);

  if (view === 'ProjectInspection' && activeProject) {
    return (
      <ProjectInspectionView
        project={activeProject}
        onBack={() => setView('dashboard')}
      />
    );
  }

  if (view === 'brandKitInspection' && activeBrandKit) {
    return (
      <BrandKitInspectionView
        brandKit={activeBrandKit}
        onBack={() => setView('dashboard')}
      />
    );
  }

  return (
    <>
      <Dashboard
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
    </>
  );
}
