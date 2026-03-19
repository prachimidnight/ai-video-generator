/**
 * Production-ready API URL Configuration
 * Returns the correct backend URL based on the environment.
 */
export const getApiUrl = () => {
    // 1. STRICTLY prioritize VITE_API_URL if it's set in Cloudflare
    if (import.meta.env.VITE_API_URL && import.meta.env.VITE_API_URL !== 'undefined') {
        return import.meta.env.VITE_API_URL.replace(/\/$/, "");
    }

    // 2. Identify environment
    const hostname = window.location.hostname;

    // Local Development
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'http://localhost:8000';
    }

    // 3. Last resort fallback (assumes backend is on same domain at /api)
    const protocol = window.location.protocol;
    const host = window.location.host;
    return `${protocol}//${host}/api`;
};

export const API_BASE_URL = getApiUrl();

export const getAuthHeaders = () => {
    const token = localStorage.getItem('access_token');
    if (!token) return {};
    return { Authorization: `Bearer ${token}` };
};
