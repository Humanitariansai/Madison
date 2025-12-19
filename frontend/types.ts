export type InspectionLevel = 'CRITICAL' | 'MEDIUM' | 'LOW' | 'PASS';

export interface BoundingBox {
  x: number;      // 0-1 relative to page width
  y: number;      // 0-1 relative to page height
  width: number;  // 0-1 relative to page width
  height: number; // 0-1 relative to page height
}

export interface InspectionResult {
  id: string;
  pageNumber: number;
  type: 'COLOR' | 'FONT' | 'LOGO' | 'SPACING' | 'IMAGERY' | 'TEXT_BODY'; // Extended types
  message: string;
  level: InspectionLevel;
  status: 'PASS' | 'FAIL';
  coordinates: BoundingBox;
}

export interface UploadedFile {
  id: string;
  name: string;
  url: string; // Blob URL
  status: 'processing' | 'ready' | 'error';
  violations: InspectionResult[];
  uploadDate: string;
}

export interface Project {
  id: string;
  title: string;
  date: string;
  status: 'COMPLIANT' | 'CRITICAL' | 'ACTION_REQUIRED';
  score: number;
  brandKit: BrandKit;
  thumbnail?: string;
  files: UploadedFile[];
}


export interface BrandKit {
  id: string;
  title: string;
  date: string;
  files: UploadedFile[];
  colors?: { name: string; hex: string; type: string }[];
  logos?: { id: string | number; name: string; url: string; variant: string }[];
  typography?: { family: string; weights: string[]; usage: string }[];
  imagery?: {}[];
}
