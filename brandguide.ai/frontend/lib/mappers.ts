import { ApiBrandKitResponse, ApiProjectResponse, BrandKit, Project, UploadedFile } from '@/types';

/**
 * Maps backend brand kit response to frontend BrandKit type
 */
export function mapApiBrandKitToFrontend(data: ApiBrandKitResponse, apiBase: string): BrandKit {
    const uploadedFiles: UploadedFile[] = (data.assets || []).map((asset) => ({
        id: asset.id,
        name: asset.filename,
        url: asset.url ? `${apiBase}${asset.url}` : '',
        status: 'ready' as const,
        violations: [],
        uploadDate: data.created_at,
    }));

    return {
        id: data.id,
        title: data.title,
        brand_name: data.brand_name,
        created_at: data.created_at,

        // Optimized Schema - direct mapping
        colors: data.colors,
        color_tolerance: data.color_tolerance,
        typography: data.typography,
        logo: data.logo,
        brand_voice: data.brand_voice,
        assets: data.assets,

        // Legacy UI fields
        files: uploadedFiles,
    };
}

/**
 * Maps backend project response to frontend Project type
 */
export function mapApiProjectToFrontend(
    data: ApiProjectResponse,
    apiBase: string,
    brandKitsMap?: Map<string, BrandKit>
): Project {
    // If project has expanded brandKit, map it
    let brandKit: BrandKit | null = null;
    if (data.brandKit) {
        brandKit = mapApiBrandKitToFrontend(data.brandKit, apiBase);
    } else if (brandKitsMap && data.brandKitId) {
        brandKit = brandKitsMap.get(data.brandKitId) || null;
    }

    return {
        id: data.id,
        title: data.title,
        date: data.date,
        status: data.status,
        score: data.score,
        brandKitId: data.brandKitId, // Map the ID directly
        brandKit: brandKit!,
        files: (data.files || []).map((f) => ({
            ...f,
            url: f.url ? `${apiBase}${f.url}` : '',
            status: 'ready' as const,
            violations: f.violations || [],
            uploadDate: data.date,
        })),
    };
}
