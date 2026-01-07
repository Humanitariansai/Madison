import React, { useState } from 'react';
import {
  Plus, Upload, Trash2, Edit2, Download,
  Type, Palette, Image as ImageIcon, LayoutGrid, FileText,
  ArrowLeft, ShieldCheck, AlertTriangle
} from 'lucide-react';
import { Button } from './ui/Button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/Badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { BrandKit } from '@/types';

// Mock Data Structure


interface props {
  brandKit: BrandKit;
  onBack: () => void;
}
export const BrandKitInspectionView: React.FC<props> = ({ brandKit, onBack }) => {
  return (

    <div className="flex flex-col h-screen bg-slate-50 overflow-hidden">
      {/* 1. Header Section */}
      <header className="bg-white border-b px-8 py-6 flex justify-between items-start flex-none z-10">
        <div>
          <div className="w-72 shrink-0 text-black p-4">
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-black-400 hover:text-slate-400 transition-colors text-sm font-medium"
            >
              <ArrowLeft size={16} /> Back to Dashboard
            </button>
          </div>
          <div className="flex items-center gap-3 mb-2">

            <h1 className="text-2xl font-bold text-slate-900">{brandKit.title}</h1>
            <Badge variant="outline" className="text-green-600 border-green-200 bg-green-50">Active</Badge>
          </div>
          <p className="text-slate-500 text-sm mb-4">
            Gold standard definition. Parsed from {brandKit.files.length} source files.
          </p>
          
          {/* Brand Voice Chips */}
          {brandKit.brand_voice_attributes && (
            <div className="flex flex-wrap gap-2">
                {brandKit.brand_voice_attributes.map(v => (
                    <Badge key={v} variant="secondary" className="bg-slate-100 text-slate-600 font-normal">
                        {v}
                    </Badge>
                ))}
                
                {brandKit.forbidden_keywords && brandKit.forbidden_keywords.length > 0 && (
                   <span className="text-xs text-red-400 flex items-center ml-2 border-l pl-3">
                     Avoid: {brandKit.forbidden_keywords.join(", ")}
                   </span>
                )}
            </div>
          )}
        </div>
        <div className="flex gap-3">
          <Button variant="outline"><Edit2 size={16} className="mr-2" /> Edit Rules</Button>
          <Button><Upload size={16} className="mr-2" /> Add Assets</Button>
        </div>
      </header>

      {/* 2. Main Content Area */}
      <div className="flex-1 flex flex-col w-full overflow-hidden">
        <Tabs defaultValue="logos" className="flex flex-col h-full w-full">
          <div className="px-8 pt-6 pb-4 flex-none">
            {/* Tabs Navigation */}
            <TabsList className="bg-white border p-1 h-12 w-full justify-start rounded-lg shadow-sm">
              <TabsTrigger value="overview" className="h-10 px-6 data-[state=active]:bg-slate-100"><FileText size={16} className="mr-2" /> Source Files</TabsTrigger>
              <TabsTrigger value="logos" className="h-10 px-6 data-[state=active]:bg-slate-100"><LayoutGrid size={16} className="mr-2" /> Logos</TabsTrigger>
              <TabsTrigger value="colors" className="h-10 px-6 data-[state=active]:bg-slate-100"><Palette size={16} className="mr-2" /> Colors</TabsTrigger>
              <TabsTrigger value="typography" className="h-10 px-6 data-[state=active]:bg-slate-100"><Type size={16} className="mr-2" /> Typography</TabsTrigger>
              <TabsTrigger value="imagery" className="h-10 px-6 data-[state=active]:bg-slate-100"><ImageIcon size={16} className="mr-2" /> Imagery</TabsTrigger>
            </TabsList>

            {/* --- TAB: LOGOS --- */}



            <TabsContent value="logos" className="flex-1 overflow-hidden mt-0 border-t border-slate-100">
              <ScrollArea className="h-full w-full">
                <div className="p-8 max-w-7xl mx-auto space-y-8">
                
                  {/* LOGO RULES SECTION */}
                  {brandKit.logo_rules && brandKit.logo_rules.length > 0 && (
                    <div className="grid md:grid-cols-2 gap-4">
                        {/* DO Rules */}
                        <Card className="border-green-100 bg-green-50/50">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-bold text-green-800 flex items-center gap-2">
                                    <ShieldCheck size={16} /> DO
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <ul className="space-y-2">
                                    {brandKit.logo_rules.filter(r => r.type === 'DO').map((r, i) => (
                                        <li key={i} className="text-sm text-green-900 flex items-start gap-2">
                                            <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-green-500 shrink-0"/> {r.rule}
                                        </li>
                                    ))}
                                </ul>
                            </CardContent>
                        </Card>
                        
                        {/* DON'T Rules */}
                        <Card className="border-red-100 bg-red-50/50">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-bold text-red-800 flex items-center gap-2">
                                    <AlertTriangle size={16} /> DON'T
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <ul className="space-y-2">
                                    {brandKit.logo_rules.filter(r => r.type === 'DONT').map((r, i) => (
                                        <li key={i} className="text-sm text-red-900 flex items-start gap-2">
                                            <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-red-500 shrink-0"/> {r.rule}
                                        </li>
                                    ))}
                                </ul>
                            </CardContent>
                        </Card>
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {/* Upload Card */}
                    <button className="border-2 border-dashed border-slate-300 rounded-xl h-64 flex flex-col items-center justify-center text-slate-400 hover:border-primary hover:bg-primary/5 hover:text-primary transition-all">
                      <Plus size={48} className="mb-4 opacity-50" />
                      <span className="font-medium">Add Logo Variant</span>
                    </button>

                    {/* Logo Cards */}
                    {brandKit.logos && brandKit.logos.map((logo) => (
                      <Card key={logo.id} className="overflow-hidden group">
                        <div className="aspect-video bg-slate-100 flex items-center justify-center p-8 relative">
                          {/* Visual Placeholder */}
                          <div className="text-4xl font-bold text-slate-300">LOGO</div>

                          {/* Overlay Actions */}
                          <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                            <Button variant="secondary" size="sm"><Download size={14} /></Button>
                            <Button variant="secondary" size="sm"><Trash2 size={14} /></Button>
                          </div>
                        </div>
                        <CardHeader className="pb-3">
                          <CardTitle className="text-base">{logo.name}</CardTitle>
                          <CardDescription>Variant: {logo.variant}</CardDescription>
                        </CardHeader>
                      </Card>
                    ))}
                  </div>
                </div>
              </ScrollArea>
            </TabsContent>

            {/* --- TAB: COLORS --- */}
            <TabsContent value="colors">
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
                {/* Use Rich Colors if available, else fall back to basic colors */}
                {(brandKit.rich_colors && brandKit.rich_colors.length > 0 ? brandKit.rich_colors : brandKit.colors)?.map((color, idx) => (
                  <div key={idx} className="group cursor-pointer">
                    <div
                      className="h-32 rounded-t-xl shadow-inner relative flex items-center justify-center border-b"
                      style={{ backgroundColor: color.hex }}
                    >
                      {/* Copy Hex on Hover */}
                      <span className="opacity-0 group-hover:opacity-100 bg-white/90 px-2 py-1 rounded text-xs font-mono font-bold shadow-sm transition-opacity">
                        {color.hex}
                      </span>
                    </div>
                    <div className="bg-white border border-t-0 p-3 rounded-b-xl shadow-sm space-y-1">
                      <div className="flex justify-between items-start">
                        <p className="font-semibold text-slate-800 text-sm truncate" title={color.name}>{color.name}</p>
                        {/* Show Usage Tag if available */}
                        {'usage' in color && color.usage && (
                          <span className="text-[10px] uppercase tracking-wider bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded">
                            {color.usage}
                          </span>
                        )}
                      </div>
                      
                      {/* Rich Data Details */}
                      {'cmyk' in color && (
                         <div className="text-[10px] text-slate-400 font-mono space-y-0.5 mt-2">
                           {color.rgb && <div className="flex justify-between"><span>RGB</span> <span>{color.rgb}</span></div>}
                           {color.cmyk && <div className="flex justify-between"><span>CMYK</span> <span>{color.cmyk}</span></div>}
                         </div>
                      )}
                      
                      {/* Fallback for basic colors */}
                      {!('cmyk' in color) && (
                         <p className="text-xs text-slate-500 capitalize">{color.type}</p>
                      )}
                    </div>
                  </div>
                ))}
                {/* Add Color Button */}
                <button className="h-full min-h-[160px] border-2 border-dashed border-slate-300 rounded-xl flex flex-col items-center justify-center text-slate-400 hover:border-primary hover:text-primary hover:bg-primary/5 transition-all">
                  <Plus size={24} className="mb-2" />
                  <span className="text-sm font-medium">Add Color</span>
                </button>
              </div>
            </TabsContent>

            {/* --- TAB: TYPOGRAPHY --- */}
            <TabsContent value="typography">
              <div className="space-y-4">
                {brandKit.typography && brandKit.typography.map((font, idx) => (
                  <Card key={idx} className="flex items-center p-6 justify-between hover:shadow-md transition-shadow">
                    <div>
                      {/* Preview of the font */}
                      <h3 className="text-4xl mb-4 text-slate-900" style={{ fontFamily: font.family }}>
                        The quick brown fox jumps over...
                      </h3>
                      <div className="flex gap-4 items-center">
                        <Badge variant="secondary" className="text-lg px-3 py-1">{font.family}</Badge>
                        <div className="text-sm text-slate-500">
                          Usage: <span className="font-medium text-slate-700">{font.use_case || font.usage || 'Primary'}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {font.weights.map(w => (
                        <div key={w} className="border rounded px-3 py-2 text-center min-w-[80px]">
                          <span className="block text-xs text-slate-400 mb-1">Weight</span>
                          <span className="font-medium text-sm text-slate-700">{w}</span>
                        </div>
                      ))}
                    </div>
                  </Card>
                ))}
              </div>
            </TabsContent>

            {/* --- TAB: OVERVIEW (Source Files) --- */}
            <TabsContent value="overview">
              <Card>
                <CardHeader>
                  <CardTitle>Source Documents</CardTitle>
                  <CardDescription>The raw files used to generate these rules.</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {brandKit.files.map((file, i) => (
                      <div key={i} className="flex items-center justify-between p-3 border rounded-lg hover:bg-slate-50">
                        <div className="flex items-center gap-4">
                          <div className="bg-red-50 p-2 rounded text-red-600">
                            <FileText size={20} />
                          </div>
                          <div>
                            <p className="font-medium text-slate-900">{file.name}</p>
                            <p className="text-xs text-slate-500">Uploaded {file.uploadDate}</p>
                          </div>
                        </div>
                        <Button variant="ghost" size="sm">Download</Button>
                      </div>
                    ))}
                  </div>
                </CardContent>
                <CardFooter className="bg-slate-50 border-t p-4">
                  <Button variant="outline" className="w-full border-dashed">
                    <Upload size={16} className="mr-2" /> Upload Updated Guidelines
                  </Button>
                </CardFooter>
              </Card>
            </TabsContent>
        
        </div>
        </Tabs>
      </div>
    </div>
  );
};
