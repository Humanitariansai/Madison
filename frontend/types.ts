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


export interface BrandColor {
  name: string;
  hex: string;
  rgb?: string;
  cmyk?: string;
  usage?: string;
  type?: string;
  text_color_rule?: string | null;
}

export interface BrandTypography {
  family: string;
  weights: string[];
  use_case?: string;
  usage?: string; // fallback
}

export interface BrandLogoRule {
  rule: string;
  type: 'DO' | 'DONT';
}

export interface BrandKit {
  id: string;
  title: string;
  date: string;
  files: UploadedFile[];

  // Basic inferred colors (backward compatibility)
  colors?: { name: string; hex: string; type: string }[];

  // Rich Data from Guidelines
  rich_colors?: BrandColor[];
  typography?: BrandTypography[];
  logo_rules?: BrandLogoRule[];
  forbidden_keywords?: string[];
  brand_voice_attributes?: string[];

  logos?: { id: string | number; name: string; url: string; variant: string }[];
  imagery?: {}[];
}
