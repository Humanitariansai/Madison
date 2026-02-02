import React from 'react'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button';
import { ChevronRight, FileText, MoreVertical, Plus, Search, ShieldCheck, FolderKanban, Folder, Forward, Trash2 } from 'lucide-react'
import { BrandKit, Project } from '@/types'
import { Input } from '@/components/ui/input';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

interface Props {
  brandKits: BrandKit[];
  projects: Project[];
  onCreateBrandKit: () => void;
  onOpenBrandKit: (brandKitId: string) => void;
}

export const BrandKitView: React.FC<Props> = ({ brandKits, projects, onCreateBrandKit, onOpenBrandKit }) => {
  const cards = brandKits.map((kit) => <Card key={kit.id} onClick={() => onOpenBrandKit(kit.id)}>
    <CardHeader>
      <CardTitle>{kit.title}</CardTitle>
    </CardHeader>
  </Card >
  )
  return <>
    {/* Top Mobile Header (only visible on small screens) */}
    <div className="md:hidden h-14 bg-white border-b flex items-center px-4 justify-between sticky top-0 z-40">
      <div className="flex items-center gap-2">
        <ShieldCheck className="text-primary" size={20} />
        <span className="font-bold">BrandGuide AI</span>
      </div>
      <Button variant="ghost" size="sm"><MoreVertical size={20} /></Button>
    </div>

    <div className="p-8 w-full space-y-8">
      {/* Filter & Toolbar */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-start">
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Search brand kits..."
            className="pl-9"
          />
        </div>
      </div>

      {/* Brand Kits Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 pb-10">
        {/* Create New Card (Quick Action) */}
        <button
          onClick={onCreateBrandKit}
          className="group border border-dashed border-slate-300 rounded-xl flex flex-col items-center justify-center h-full min-h-[300px] hover:border-primary hover:bg-muted/50 transition-all gap-4 bg-muted/20"
        >
          <div className="bg-background p-4 rounded-full shadow-sm group-hover:scale-110 transition-transform duration-300">
            <Plus className="h-6 w-6 text-muted-foreground group-hover:text-primary" />
          </div>
          <p className="font-medium text-muted-foreground group-hover:text-primary transition-colors">Create New Brand Kit</p>
        </button>

        {/* Brand Kit Cards */}
        {brandKits.map((brandKit) => (
          <Card
            key={brandKit.id}
            className="cursor-pointer hover:shadow-md hover:border-primary/50 transition-all duration-300 group overflow-hidden"
            onClick={() => onOpenBrandKit(brandKit.id)}
          >
            <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
              <div className="space-y-1 max-w-[70%]">
                <CardTitle className="text-base font-semibold group-hover:text-primary transition-colors truncate" title={brandKit.title}>
                  {brandKit.title}
                </CardTitle>
                <CardDescription className="text-xs">{brandKit.created_at}</CardDescription>
              </div>
              <div onClick={(e) => e.stopPropagation()}>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground">
                      <MoreVertical size={16} />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-48">
                    <DropdownMenuItem>
                      <Folder className="text-muted-foreground" />
                      <span>View Brand Kit</span>
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <Forward className="text-muted-foreground" />
                      <span>Share Brand Kit</span>
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem>
                      <Trash2 className="text-muted-foreground" />
                      <span>Delete Brand Kit</span>
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </CardHeader>

            <CardContent>
              {/* Visual Preview Placeholder - Brand Kits don't have thumbnails yet */}
              <div className="aspect-video bg-muted rounded-md flex items-center justify-center mb-6 border border-border relative overflow-hidden group-hover:shadow-inner transition-all">
                <div className="flex flex-col items-center gap-2">
                  <FileText className="h-10 w-10 text-muted-foreground/50 group-hover:scale-110 transition-transform duration-500" />
                  <span className="text-[10px] text-muted-foreground/50 font-mono">BRAND KIT</span>
                </div>
                <div className="absolute inset-0 bg-transparent group-hover:bg-black/5 transition-colors" />
              </div>
            </CardContent>

            <CardFooter className="border-t bg-muted/50 p-3 px-6">
              <div className="flex items-center gap-2 text-xs text-muted-foreground w-full">
                <FolderKanban size={14} className="text-primary" />
                <span className="truncate flex-1" title={brandKit.title}>
                  {projects.filter(p => p.brandKitId === brandKit.id).length} Associated Projects
                </span>
                <ChevronRight size={14} className="text-muted-foreground/50 group-hover:text-primary group-hover:translate-x-1 transition-all" />
              </div>
            </CardFooter>
          </Card>
        ))}
      </div>

      {brandKits.length === 0 && (
        <div className="text-center py-20 bg-white rounded-xl border border-dashed border-slate-200">
          <p className="text-slate-500">No brand kits found. Create your first brand kit to get started.</p>
        </div>
      )}
    </div>
  </>
}
