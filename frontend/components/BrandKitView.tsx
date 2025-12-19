import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from './ui/Button'
import { AlertTriangle, BarChart3, Bell, ChevronRight, FileText, MoreVertical, Plus, Search, ShieldCheck } from 'lucide-react'
import { BrandKit } from '@/types'
import { Input } from './ui/Input'
import { Progress } from './ui/Progress'
import { Separator } from './ui/Separator'
import { Badge } from './ui/Badge'

interface Props {
  brandKits: BrandKit[];
  onCreateBrandKit: () => void;
  onOpenBrandKit: (brandKitId: string) => void;
}

export const BrandKitView: React.FC<Props> = ({brandKits, onCreateBrandKit, onOpenBrandKit}) => {
  const cards = brandKits.map((kit) => <Card key={kit.id}onClick={() => onOpenBrandKit(kit.id)}>
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
        <span className="font-bold">Brand Guard AI</span>
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
          <Button onClick={onCreateBrandKit} className="gap-2 shadow-sm shadow-primary/20">
            <Plus size={16} /> New Brand Kit
          </Button>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Brand Kits</CardTitle>
            <FileText className="h-4 w-4 text-slate-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{brandKits.length}</div>
            <p className="text-xs text-slate-500">+2 from last month</p>
          </CardContent>
        </Card>
      </div>

      <Separator />

      {/* Filter & Toolbar */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold">Your Brand Kits</h2>
          <Badge variant="secondary" className="ml-2">{brandKits.length}</Badge>
        </div>

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
          className="group border-2 border-dashed border-slate-300 rounded-xl flex flex-col items-center justify-center h-full min-h-[300px] hover:border-primary hover:bg-primary/5 transition-all gap-4 bg-white/50"
        >
          <div className="bg-slate-100 p-4 rounded-full group-hover:bg-primary/10 group-hover:shadow-sm transition-colors">
            <Plus className="h-8 w-8 text-slate-400 group-hover:text-primary" />
          </div>
          <p className="font-medium text-slate-600 group-hover:text-primary">Create New Brand Kit</p>
        </button>

        {/* Brand Kit Cards */}
        {brandKits.map((brandKit) => (
          <Card
            key={brandKit.id}
            className="cursor-pointer hover:shadow-lg hover:border-primary/30 transition-all duration-300 border-slate-200 group overflow-hidden"
            onClick={() => onOpenBrandKit(brandKit.id)}
          >
            <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
              <div className="space-y-1 max-w-[70%]">
                <CardTitle className="text-base font-semibold group-hover:text-primary transition-colors truncate" title={brandKit.title}>
                  {brandKit.title}
                </CardTitle>
                <CardDescription className="text-xs">{brandKit.date}</CardDescription>
              </div>
            </CardHeader>

            <CardContent>
              {/* Visual Preview Placeholder */}
              <div className="aspect-video bg-slate-100 rounded-md flex items-center justify-center mb-6 border border-slate-200 relative overflow-hidden group-hover:shadow-inner transition-all">
                {brandKit.thumbnail ? (
                  <img src={brandKit.thumbnail} alt="Preview" className="w-full h-full object-cover opacity-90" />
                ) : (
                  <div className="flex flex-col items-center gap-2">
                    <FileText className="h-10 w-10 text-slate-300 group-hover:scale-110 transition-transform duration-500" />
                    <span className="text-[10px] text-slate-400 font-mono">PDF PREVIEW</span>
                  </div>
                )}
                {/* Hover Overlay */}
                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors" />
              </div>
            </CardContent>

            <CardFooter className="border-t bg-slate-50/50 p-3 px-6">
              <div className="flex items-center gap-2 text-xs text-slate-500 w-full">
                <ShieldCheck size={14} className="text-primary" />
                <span className="truncate flex-1" title={brandKit.title}>{brandKit.title}</span>
                <ChevronRight size={14} className="text-slate-300 group-hover:text-primary group-hover:translate-x-1 transition-all" />
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

type Props2 = {
  brandKits: BrandKit[];
  setBrandKits: React.Dispatch<React.SetStateAction<any[]>>;
};
