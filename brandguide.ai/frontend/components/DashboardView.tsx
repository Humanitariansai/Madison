import React from 'react'
import { ShieldCheck, MoreVertical, Bell, Plus, FileText, BarChart3, AlertTriangle, Search, ChevronRight, Palette } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import { Project } from '@/types'
import { Badge } from '@/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

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

  return (
    <div className="p-8 w-full space-y-8">
      <div className="space-y-4">
        {/* Stats Row - Meaningful Analytics */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Compliance Score</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{avgScore}%</div>
              <p className="text-xs text-muted-foreground mt-1">
                <span className="text-green-600 font-medium">↑ 4.5%</span> from last week
              </p>
              <Progress value={avgScore} className="h-1 mt-3" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Top Violations</CardTitle>
              <AlertTriangle className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{criticalProjects} Critical</div>
              <div className="mt-3 space-y-1">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Logo Misuse</span>
                  <span className="font-medium text-foreground">12</span>
                </div>
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Color Contrast</span>
                  <span className="font-medium text-foreground">8</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Asset Usage</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">1,248</div>
              <p className="text-xs text-muted-foreground mt-1">
                Assets scanned this month
              </p>
              <div className="flex gap-1 mt-3 h-1.5 overflow-hidden rounded-full">
                <div className="bg-primary w-[60%]" />
                <div className="bg-primary/50 w-[25%]" />
                <div className="bg-primary/20 w-[15%]" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Brand Kits</CardTitle>
              <ShieldCheck className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">7</div>
              <p className="text-xs text-muted-foreground mt-1">
                Used in {totalProjects} projects
              </p>
              <div className="mt-3 text-xs text-muted-foreground flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-500" />
                All kits up to date
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
          <Card className="col-span-4 lg:col-span-7">
            <CardHeader className='flex flex-row items-center justify-between'>
              <div className='space-y-1.5'>
                <CardTitle>Recent Projects</CardTitle>
                <CardDescription>
                  You have {projects.length} active projects managed by your team.
                </CardDescription>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 pb-4">

                {/* Create New Card (Quick Action) */}
                <button
                  onClick={onCreateProject}
                  className="group border border-dashed border-slate-300 rounded-xl flex flex-col items-center justify-center h-full min-h-[300px] hover:border-primary hover:bg-muted/50 transition-all gap-4 bg-muted/20"
                >
                  <div className="bg-background p-4 rounded-full shadow-sm group-hover:scale-110 transition-transform duration-300">
                    <Plus className="h-6 w-6 text-muted-foreground group-hover:text-primary" />
                  </div>
                  <p className="font-medium text-muted-foreground group-hover:text-primary transition-colors">Create New Project</p>
                </button>

                {/* Project Cards */}
                {projects.map((project) => (
                  <Card
                    key={project.id}
                    className="cursor-pointer hover:shadow-md hover:border-primary/50 transition-all duration-300 group overflow-hidden"
                    onClick={() => onOpenProject(project.id)}
                  >
                    <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                      <div className="space-y-1 max-w-[70%]">
                        <CardTitle className="text-base font-semibold group-hover:text-primary transition-colors truncate" title={project.title}>
                          {project.title}
                        </CardTitle>
                        <CardDescription className="text-xs">{project.date}</CardDescription>
                      </div>
                      <div className="flex gap-2 items-center" onClick={(e) => e.stopPropagation()}>
                        <Badge variant={
                          project.status === 'COMPLIANT' ? 'default' : // changed success to default for neutral theme
                            project.status === 'CRITICAL' ? 'destructive' : 'secondary'
                        } className={project.status === 'COMPLIANT' ? 'bg-green-600 hover:bg-green-700' : ''}>
                          {/* Manually overriding compliant color if needed, or stick to neutral 'default' */}
                          {project.status === 'COMPLIANT' ? 'Passed' :
                            project.status === 'CRITICAL' ? 'Critical' : 'Review'}
                        </Badge>

                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground">
                              <MoreVertical size={16} />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem>Edit Project</DropdownMenuItem>
                            <DropdownMenuItem>Duplicate</DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem className="text-red-600">Delete</DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </CardHeader>

                    <CardContent>
                      {/* Visual Preview Placeholder */}
                      <div className="aspect-video bg-muted rounded-md flex items-center justify-center mb-6 border border-border relative overflow-hidden group-hover:shadow-inner transition-all">
                        {project.thumbnail ? (
                          <img src={project.thumbnail} alt="Preview" className="w-full h-full object-cover opacity-90" />
                        ) : (
                          <div className="flex flex-col items-center gap-2">
                            <FileText className="h-10 w-10 text-muted-foreground/50 group-hover:scale-110 transition-transform duration-500" />
                            <span className="text-[10px] text-muted-foreground/50 font-mono">PDF PREVIEW</span>
                          </div>
                        )}
                        {/* Hover Overlay */}
                        <div className="absolute inset-0 bg-transparent group-hover:bg-black/5 transition-colors" />
                      </div>

                      {/* Score Indicator */}
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground font-medium text-xs uppercase tracking-wide">Brand Score</span>
                          <span className={`font-bold ${project.score >= 90 ? 'text-green-600' :
                            project.score >= 70 ? 'text-amber-600' : 'text-red-600'
                            }`}>{project.score}%</span>
                        </div>
                        <Progress value={project.score} className="h-2" />
                      </div>
                    </CardContent>

                    <CardFooter className="border-t bg-muted/50 p-3 px-6">
                      <div className="flex items-center gap-2 text-xs text-muted-foreground w-full">
                        <Palette size={14} className="text-primary" />
                        <span className="truncate flex-1" title={project.brandKit?.title || 'Unknown Brand Kit'}>{project.brandKit?.title || 'Loading...'}</span>
                        <ChevronRight size={14} className="text-muted-foreground/50 group-hover:text-primary group-hover:translate-x-1 transition-all" />
                      </div>
                    </CardFooter>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {
          projects.length === 0 && (
            <div className="text-center py-20 bg-white rounded-xl border border-dashed border-slate-200">
              <p className="text-slate-500">No projects found. Create your first project to get started.</p>
            </div>
          )
        }
      </div>
    </div>
  );
}
