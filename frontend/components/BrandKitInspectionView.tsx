import React from 'react';
import {
  Plus, Upload, Trash2, Download,
  Type, Palette, Image as ImageIcon, LayoutGrid, FileText,
  ShieldCheck, AlertTriangle
} from 'lucide-react';
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { BrandKit } from '@/types';


interface props {
  brandKit: BrandKit;
  onBack: () => void;
}

export const BrandKitInspectionView: React.FC<props> = ({ brandKit }) => {
  console.log("viewing brandkit", brandKit);
  return (
    <div className="flex flex-col h-full bg-background overflow-hidden animate-in fade-in duration-300">
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col w-full overflow-hidden">
        <Tabs defaultValue="logos" className="flex flex-col h-full w-full">

          {/* Tabs Navigation */}
          <div className="border-b px-6 bg-muted/40 flex-none">
            <TabsList className="bg-transparent p-0 h-10 w-full justify-start gap-6 rounded-none">
              <TabsTrigger
                value="overview"
                className="relative h-10 rounded-none border-b-2 border-b-transparent bg-transparent px-2 pb-3 pt-2 font-medium text-muted-foreground shadow-none transition-none data-[state=active]:border-b-primary data-[state=active]:text-foreground data-[state=active]:shadow-none"
              >
                <FileText size={16} className="mr-2" /> Source Files
              </TabsTrigger>
              <TabsTrigger
                value="logos"
                className="relative h-10 rounded-none border-b-2 border-b-transparent bg-transparent px-2 pb-3 pt-2 font-medium text-muted-foreground shadow-none transition-none data-[state=active]:border-b-primary data-[state=active]:text-foreground data-[state=active]:shadow-none"
              >
                <LayoutGrid size={16} className="mr-2" /> Logos
              </TabsTrigger>
              <TabsTrigger
                value="colors"
                className="relative h-10 rounded-none border-b-2 border-b-transparent bg-transparent px-2 pb-3 pt-2 font-medium text-muted-foreground shadow-none transition-none data-[state=active]:border-b-primary data-[state=active]:text-foreground data-[state=active]:shadow-none"
              >
                <Palette size={16} className="mr-2" /> Colors
              </TabsTrigger>
              <TabsTrigger
                value="typography"
                className="relative h-10 rounded-none border-b-2 border-b-transparent bg-transparent px-2 pb-3 pt-2 font-medium text-muted-foreground shadow-none transition-none data-[state=active]:border-b-primary data-[state=active]:text-foreground data-[state=active]:shadow-none"
              >
                <Type size={16} className="mr-2" /> Typography
              </TabsTrigger>
              <TabsTrigger
                value="imagery"
                className="relative h-10 rounded-none border-b-2 border-b-transparent bg-transparent px-2 pb-3 pt-2 font-medium text-muted-foreground shadow-none transition-none data-[state=active]:border-b-primary data-[state=active]:text-foreground data-[state=active]:shadow-none"
              >
                <ImageIcon size={16} className="mr-2" /> Imagery
              </TabsTrigger>
            </TabsList>
          </div>

          {/* --- TAB: OVERVIEW (Source Files) --- */}
          <TabsContent value="overview" className="flex-1 overflow-hidden mt-0 data-[state=active]:flex flex-col">
            <ScrollArea className="h-full w-full">
              <div className="p-6 max-w-5xl mx-auto space-y-6">
                <div className="space-y-1">
                  <h3 className="text-lg font-medium">Brand Definition</h3>
                  <p className="text-sm text-muted-foreground">
                    Parsed from {brandKit.files.length} source files to invoke the brand voice.
                  </p>
                </div>

                {/* Brand Voice Chips */}
                {brandKit.brand_voice_attributes && (
                  <div className="flex flex-wrap gap-2 mb-6">
                    {brandKit.brand_voice_attributes.map(v => (
                      <Badge key={v} variant="secondary" className="px-3 py-1 font-normal">
                        {v}
                      </Badge>
                    ))}

                    {brandKit.forbidden_keywords && brandKit.forbidden_keywords.length > 0 && (
                      <div className="flex items-center gap-2 ml-2 border-l pl-4">
                        <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Avoid</span>
                        <div className="flex gap-1">
                          {brandKit.forbidden_keywords.map(k => (
                            <Badge key={k} variant="outline" className="text-red-500 border-red-200 bg-red-50 hover:bg-red-50">
                              {k}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                <Card>
                  <CardHeader>
                    <CardTitle>Source Documents</CardTitle>
                    <CardDescription>The raw files used to generate these rules.</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {brandKit.files.map((file, i) => (
                        <div key={i} className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors">
                          <div className="flex items-center gap-4">
                            <div className="bg-muted p-2 rounded text-muted-foreground">
                              <FileText size={20} />
                            </div>
                            <div>
                              <p className="font-medium text-foreground">{file.name}</p>
                              <p className="text-xs text-muted-foreground">Uploaded {file.uploadDate}</p>
                            </div>
                          </div>
                          <Button variant="ghost" size="sm">Download</Button>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                  <CardFooter className="bg-muted/30 border-t p-4">
                    <Button variant="outline" className="w-full border-dashed">
                      <Upload size={16} className="mr-2" /> Upload Updated Guidelines
                    </Button>
                  </CardFooter>
                </Card>
              </div>
            </ScrollArea>
          </TabsContent>


          {/* --- TAB: LOGOS --- */}
          <TabsContent value="logos" className="flex-1 overflow-hidden mt-0 data-[state=active]:flex flex-col">
            <ScrollArea className="h-full w-full">
              <div className="p-6 max-w-7xl mx-auto space-y-8">

                {/* LOGO RULES SECTION */}
                {brandKit.logo_rules && brandKit.logo_rules.length > 0 && (
                  <div className="grid md:grid-cols-2 gap-4">
                    {/* DO Rules */}
                    <Card className="border-green-200 bg-green-50/10">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-bold text-green-700 flex items-center gap-2">
                          <ShieldCheck size={16} /> DO
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ul className="space-y-2">
                          {brandKit.logo_rules.filter(r => r.type === 'DO').map((r, i) => (
                            <li key={i} className="text-sm text-foreground flex items-start gap-2">
                              <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-green-500 shrink-0" /> {r.rule}
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>

                    {/* DON'T Rules */}
                    <Card className="border-red-200 bg-red-50/10">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-bold text-red-700 flex items-center gap-2">
                          <AlertTriangle size={16} /> DON'T
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ul className="space-y-2">
                          {brandKit.logo_rules.filter(r => r.type === 'DONT').map((r, i) => (
                            <li key={i} className="text-sm text-foreground flex items-start gap-2">
                              <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-red-500 shrink-0" /> {r.rule}
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {/* Upload Card */}
                  <button className="group border border-dashed border-slate-300 rounded-xl h-64 flex flex-col items-center justify-center bg-muted/20 hover:border-primary hover:bg-muted/50 transition-all gap-4">
                    <div className="bg-background p-4 rounded-full shadow-sm group-hover:scale-110 transition-transform duration-300">
                      <Plus className="h-6 w-6 text-muted-foreground group-hover:text-primary" />
                    </div>
                    <p className="font-medium text-muted-foreground group-hover:text-primary transition-colors">Add Logo Variant</p>
                  </button>

                  {/* Logo Cards */}
                  {brandKit.logos && brandKit.logos.map((logo) => (
                    <Card key={logo.id} className="overflow-hidden group hover:shadow-md transition-all">
                      <div className="aspect-video bg-muted/30 flex items-center justify-center p-8 relative border-b">
                        {/* Visual Placeholder */}
                        <div className="text-4xl font-bold text-muted-foreground/20">LOGO</div>

                        {/* Overlay Actions */}
                        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                          <Button variant="secondary" size="sm" className="h-8 w-8 p-0"><Download size={14} /></Button>
                          <Button variant="destructive" size="sm" className="h-8 w-8 p-0"><Trash2 size={14} /></Button>
                        </div>
                      </div>
                      <CardHeader className="pb-3 pt-3">
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
          <TabsContent value="colors" className="flex-1 overflow-hidden mt-0 data-[state=active]:flex flex-col">
            <ScrollArea className="h-full w-full">
              <div className="p-6 max-w-7xl mx-auto">
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
                  {/* Use Rich Colors if available, else fall back to basic colors */}
                  {(brandKit.rich_colors && brandKit.rich_colors.length > 0 ? brandKit.rich_colors : brandKit.colors)?.map((color, idx) => (
                    <div key={idx} className="group cursor-pointer">
                      <div
                        className="h-32 rounded-t-xl shadow-inner relative flex items-center justify-center border-b"
                        style={{ backgroundColor: color.hex }}
                      >
                        {/* Copy Hex on Hover */}
                        <span className="opacity-0 group-hover:opacity-100 bg-background/90 px-2 py-1 rounded text-xs font-mono font-bold shadow-sm transition-opacity">
                          {color.hex}
                        </span>
                      </div>
                      <div className="bg-card border border-t-0 p-3 rounded-b-xl shadow-sm space-y-1">
                        <div className="flex justify-between items-start">
                          <p className="font-semibold text-foreground text-sm truncate" title={color.name}>{color.name}</p>
                          {/* Show Usage Tag if available */}
                          {'usage' in color && color.usage && (
                            <span className="text-[10px] uppercase tracking-wider bg-muted text-muted-foreground px-1.5 py-0.5 rounded">
                              {color.usage}
                            </span>
                          )}
                        </div>

                        {/* Rich Data Details */}
                        {'cmyk' in color && (
                          <div className="text-[10px] text-muted-foreground font-mono space-y-0.5 mt-2">
                            {color.rgb && <div className="flex justify-between"><span>RGB</span> <span>{color.rgb}</span></div>}
                            {color.cmyk && <div className="flex justify-between"><span>CMYK</span> <span>{color.cmyk}</span></div>}
                          </div>
                        )}

                        {/* Fallback for basic colors */}
                        {!('cmyk' in color) && (
                          <p className="text-xs text-muted-foreground capitalize">{color.type}</p>
                        )}
                      </div>
                    </div>
                  ))}
                  {/* Add Color Button */}
                  <button className="group h-full min-h-[160px] border border-dashed border-slate-300 rounded-xl flex flex-col items-center justify-center bg-muted/20 hover:border-primary hover:bg-muted/50 transition-all gap-2">
                    <div className="bg-background p-2 rounded-full shadow-sm group-hover:scale-110 transition-transform duration-300">
                      <Plus size={20} className="text-muted-foreground group-hover:text-primary" />
                    </div>
                    <span className="text-sm font-medium text-muted-foreground group-hover:text-primary transition-colors">Add Color</span>
                  </button>
                </div>
              </div>
            </ScrollArea>
          </TabsContent>

          {/* --- TAB: TYPOGRAPHY --- */}
          <TabsContent value="typography" className="flex-1 overflow-hidden mt-0 data-[state=active]:flex flex-col">
            <ScrollArea className="h-full w-full">
              <div className="p-6 max-w-5xl mx-auto space-y-4">
                {brandKit.typography && brandKit.typography.map((font, idx) => (
                  <Card key={idx} className="flex items-center p-6 justify-between hover:shadow-md transition-shadow">
                    <div>
                      {/* Preview of the font */}
                      <h3 className="text-4xl mb-4 text-foreground" style={{ fontFamily: font.family }}>
                        The quick brown fox jumps over...
                      </h3>
                      <div className="flex gap-4 items-center">
                        <Badge variant="secondary" className="text-lg px-3 py-1 bg-muted">{font.family}</Badge>
                        <div className="text-sm text-muted-foreground">
                          Usage: <span className="font-medium text-foreground">{font.use_case || font.usage || 'Primary'}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {font.weights.map(w => (
                        <div key={w} className="border rounded px-3 py-2 text-center min-w-[80px] bg-muted/10">
                          <span className="block text-xs text-muted-foreground mb-1">Weight</span>
                          <span className="font-medium text-sm text-foreground">{w}</span>
                        </div>
                      ))}
                    </div>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="imagery" className="flex-1 overflow-hidden mt-0 data-[state=active]:flex flex-col">
            <ScrollArea className="h-full w-full">
              <div className="p-6 max-w-5xl mx-auto flex flex-col items-center justify-center text-center py-20 text-muted-foreground">
                <ImageIcon size={48} className="mb-4 opacity-20" />
                <h3 className="text-lg font-medium text-foreground">Imagery Guidelines</h3>
                <p className="max-w-md mt-2">Upload example images to define photography styles, watermarking rules, and usage restrictions.</p>
                <Button className="mt-6" variant="outline">
                  <Upload size={16} className="mr-2" /> Upload Imagery Assets
                </Button>
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};
