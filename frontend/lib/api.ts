// Centralized API configuration
// Centralized API configuration
export const API_BASE = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';

/**
 * Utility function to construct API URLs
 */
export function apiUrl(path: string): string {
    return `${API_BASE}${path}`;
}
