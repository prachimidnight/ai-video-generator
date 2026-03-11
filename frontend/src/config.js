/**
 * Production-ready API URL Configuration
 * Returns the correct backend URL based on the environment.
 */
export const getApiUrl = () => {
    // 1. Check for VITE_API_URL (set during npm run build)
    if (import.meta.env.VITE_API_URL) {
        return import.meta.env.VITE_API_URL;
    }

    // 2. Identify environment
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    const host = window.location.host;

    // Local Development
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'http://localhost:8000';
    }

    // Production Fallback
    // If you host backend on the same domain at /api (common in Cloudflare)
    // Example: https://ai-video-generator.prachi-0eb.workers.dev/api
    return `${protocol}//${host}/api`;
};

export const API_BASE_URL = getApiUrl();
