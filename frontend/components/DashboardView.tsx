import React from 'react'
import { ShieldCheck, MoreVertical, Bell, Plus, FileText, BarChart3, AlertTriangle, Search, ChevronRight } from 'lucide-react'
import { Button } from './ui/Button'
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from '@/components/ui/card'
import { Input } from './ui/Input'
import { Progress } from './ui/Progress'
import { Separator } from './ui/Separator'
import { Project } from '@/types'
import { Badge } from './ui/Badge'

interface Props {
  onCreateProject: () => void;
  onOpenProject: (projectId: string) => void;
  projects: Project[];
}

export const DashboardView: React.FC<Props> = ({ onCreateProject, onOpenProject, projects }) => {
  // Calculated stats
  const totalProjects = projects.length;
  const criticalProjects = projects.filter(p => p.status === 'CRITICAL').length;
  const avgScore = totalProjects > 0
    ? Math.round(projects.reduce((acc, curr) => acc + curr.score, 0) / totalProjects)
    : 0;

  return <>
    {/* Top Mobile Header (only visible on small screens) */}
    <div className="md:hidden h-14 bg-white border-b flex items-center px-4 justify-between sticky top-0 z-40">
      <div className="flex items-center gap-2">
        <ShieldCheck className="text-primary" size={20} />
        <span className="font-bold">Brand Guide AI</span>
      </div>
      <Button variant="ghost" size="sm"><MoreVertical size={20} /></Button>
    </div>

    <div className="p-8 max-w-7xl mx-auto w-full space-y-8">

      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Overview</h1>
          <p className="text-slate-500 mt-1">Welcome back, John. Here's what needs attention today.</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" className="gap-2 bg-white">
            <Bell size={16} /> <span className="hidden sm:inline">Notifications</span>
          </Button>
          <Button onClick={onCreateProject} className="gap-2 shadow-sm shadow-primary/20">
            <Plus size={16} /> New Project
          </Button>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Projects</CardTitle>
            <FileText className="h-4 w-4 text-slate-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalProjects}</div>
            <p className="text-xs text-slate-500">+2 from last month</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Compliance</CardTitle>
            <BarChart3 className="h-4 w-4 text-slate-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{avgScore}%</div>
            <p className="text-xs text-slate-500">
              {avgScore > 80 ? 'Healthy metrics' : 'Attention needed'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Critical Issues</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{criticalProjects}</div>
            <p className="text-xs text-slate-500">Action items pending</p>
          </CardContent>
        </Card>
      </div>

      <Separator />

      {/* Filter & Toolbar */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold">Recent Projects</h2>
          <Badge variant="secondary" className="ml-2">{projects.length}</Badge>
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Search projects..."
            className="pl-9"
          />
        </div>
      </div>

      {/* Project Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 pb-10">

        {/* Create New Card (Quick Action) */}
        <button
          onClick={onCreateProject}
          className="group border-2 border-dashed border-slate-300 rounded-xl flex flex-col items-center justify-center h-full min-h-[300px] hover:border-primary hover:bg-primary/5 transition-all gap-4 bg-white/50"
        >
          <div className="bg-slate-100 p-4 rounded-full group-hover:bg-primary/10 group-hover:shadow-sm transition-colors">
            <Plus className="h-8 w-8 text-slate-400 group-hover:text-primary" />
          </div>
          <p className="font-medium text-slate-600 group-hover:text-primary">Create New Project</p>
        </button>

        {/* Project Cards */}
        {projects.map((project) => (
          <Card
            key={project.id}
            className="cursor-pointer hover:shadow-lg hover:border-primary/30 transition-all duration-300 border-slate-200 group overflow-hidden"
            onClick={() => onOpenProject(project.id)}
          >
            <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
              <div className="space-y-1 max-w-[70%]">
                <CardTitle className="text-base font-semibold group-hover:text-primary transition-colors truncate" title={project.title}>
                  {project.title}
                </CardTitle>
                <CardDescription className="text-xs">{project.date}</CardDescription>
              </div>
              <Badge variant={
                project.status === 'COMPLIANT' ? 'success' :
                  project.status === 'CRITICAL' ? 'destructive' : 'secondary'
              }>
                {project.status === 'COMPLIANT' ? 'Passed' :
                  project.status === 'CRITICAL' ? 'Critical' : 'Review'}
              </Badge>
            </CardHeader>

            <CardContent>
              {/* Visual Preview Placeholder */}
              <div className="aspect-video bg-slate-100 rounded-md flex items-center justify-center mb-6 border border-slate-200 relative overflow-hidden group-hover:shadow-inner transition-all">
                {project.thumbnail ? (
                  <img src={project.thumbnail} alt="Preview" className="w-full h-full object-cover opacity-90" />
                ) : (
                  <div className="flex flex-col items-center gap-2">
                    <FileText className="h-10 w-10 text-slate-300 group-hover:scale-110 transition-transform duration-500" />
                    <span className="text-[10px] text-slate-400 font-mono">PDF PREVIEW</span>
                  </div>
                )}
                {/* Hover Overlay */}
                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors" />
              </div>

              {/* Score Indicator */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500 font-medium text-xs uppercase tracking-wide">Brand Score</span>
                  <span className={`font-bold ${project.score >= 90 ? 'text-green-600' :
                    project.score >= 70 ? 'text-amber-600' : 'text-red-600'
                    }`}>{project.score}%</span>
                </div>
                <Progress value={project.score} />
              </div>
            </CardContent>

            <CardFooter className="border-t bg-slate-50/50 p-3 px-6">
              <div className="flex items-center gap-2 text-xs text-slate-500 w-full">
                <ShieldCheck size={14} className="text-primary" />
                <span className="truncate flex-1" title={project.brandKit?.title || 'Unknown Brand Kit'}>{project.brandKit?.title || 'Loading...'}</span>
                <ChevronRight size={14} className="text-slate-300 group-hover:text-primary group-hover:translate-x-1 transition-all" />
              </div>
            </CardFooter>
          </Card>
        ))}
      </div>

      {projects.length === 0 && (
        <div className="text-center py-20 bg-white rounded-xl border border-dashed border-slate-200">
          <p className="text-slate-500">No projects found. Create your first project to get started.</p>
        </div>
      )}
    </div>
  </>
}
