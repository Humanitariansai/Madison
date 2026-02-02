import React from 'react'
import { MoreVertical, Plus, FileText, Search, ChevronRight, Palette, Folder, Forward, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input';
import { Project } from '@/types'
import { Badge } from './ui/badge'
import { Progress } from '@/components/ui/progress'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

interface Props {
    projects: Project[];
    onCreateProject: () => void;
    onOpenProject: (projectId: string) => void;
}

export const ProjectsView: React.FC<Props> = ({ projects, onCreateProject, onOpenProject }) => {

    return (
        <div className="p-8 w-full space-y-8">
            <div className="flex flex-col sm:flex-row gap-4 items-center justify-start">
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
                                    project.status === 'COMPLIANT' ? 'default' :
                                        project.status === 'CRITICAL' ? 'destructive' : 'secondary'
                                } className={project.status === 'COMPLIANT' ? 'bg-green-600 hover:bg-green-700' : ''}>
                                    {project.status === 'COMPLIANT' ? 'Passed' :
                                        project.status === 'CRITICAL' ? 'Critical' : 'Review'}
                                </Badge>
                                <DropdownMenu>
                                    <DropdownMenuTrigger asChild>
                                        <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground">
                                            <MoreVertical size={16} />
                                        </Button>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent align="end" className="w-48">
                                        <DropdownMenuItem>
                                            <Folder className="text-muted-foreground" />
                                            <span>View Project</span>
                                        </DropdownMenuItem>
                                        <DropdownMenuItem>
                                            <Forward className="text-muted-foreground" />
                                            <span>Share Project</span>
                                        </DropdownMenuItem>
                                        <DropdownMenuSeparator />
                                        <DropdownMenuItem>
                                            <Trash2 className="text-muted-foreground" />
                                            <span>Delete Project</span>
                                        </DropdownMenuItem>
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
        </div>
    );
}
