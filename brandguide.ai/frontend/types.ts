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
  type: 'PALETTE' | 'TYPOGRAPHY' | 'LOGO' | 'SPACING' | 'IMAGERY' | 'TEXT_BODY'; // Extended types
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
  brandKitId: string; // Added for easier filtering
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
  is_uploaded?: boolean;
}

export interface BrandLogoRule {
  rule: string;
  type: 'DO' | 'DONT';
}

export interface BrandLogo {
  allowed_ratios?: number[];
  rules?: BrandLogoRule[];
  primary_asset_id?: string;
  variants?: string[];
}

export interface BrandVoice {
  attributes?: string[];
  forbidden_keywords?: string[];
  frequent_keywords?: string[];
}

export interface BrandKit {
  id: string;
  title: string;
  brand_name?: string;
  created_at: string;

  // Optimized Schema
  colors?: BrandColor[];           // Unified colors
  color_tolerance?: number;
  typography?: BrandTypography[];
  logo?: BrandLogo;
  logo_rules?: BrandLogo;          // Backend sends this as dict, mapped to BrandLogo interface
  brand_voice?: BrandVoice;
  assets?: ApiAsset[];

  // UI-specific computed fields
  files?: UploadedFile[];  // Legacy mapping
}

// ===== API Response Types =====
// These types represent the shape of data coming from the backend API

export interface ApiAsset {
  id: string;
  filename: string;
  category: 'LOGO' | 'FONT' | 'GUIDELINES' | 'IMAGERY' | 'TEMPLATE' | 'DOCUMENT' | 'OTHER';
  path: string;
  url: string;
  metadata?: Record<string, any>;
}

export interface ApiBrandKitResponse {
  id: string;
  title: string;
  brand_name: string;
  created_at: string;

  // Optimized Schema
  colors: BrandColor[];
  color_tolerance: number;
  typography: BrandTypography[];
  logo: BrandLogo;
  brand_voice: BrandVoice;
  assets: ApiAsset[];
}

export interface ApiProjectFile {
  id: string;
  name: string;
  url: string;
  violations?: InspectionResult[];
}

export interface ApiProjectResponse {
  id: string;
  title: string;
  date: string;
  status: 'COMPLIANT' | 'CRITICAL' | 'ACTION_REQUIRED';
  score: number;
  brandKitId: string;
  brandKit?: ApiBrandKitResponse; // When using ?expand=brandKit
  files?: ApiProjectFile[];
}
