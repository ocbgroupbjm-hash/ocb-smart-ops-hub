// OCB TITAN ERP - Centralized API URL Configuration
// Supports both preview domain and custom domains

/**
 * Get the appropriate API base URL
 * - On preview domain: uses REACT_APP_BACKEND_URL
 * - On custom domain: uses relative path for proxy routing
 */
export const getApiUrl = () => {
  const envUrl = process.env.REACT_APP_BACKEND_URL;
  
  // If no env URL configured, use relative path
  if (!envUrl) return '';
  
  // Check if we're on the preview domain
  const isPreviewDomain = window.location.hostname.includes('preview.emergentagent.com');
  
  // On custom domain, use relative path (proxy handles routing)
  if (!isPreviewDomain) {
    return '';
  }
  
  return envUrl;
};

// Export as default for backward compatibility
export const API_URL = getApiUrl();

export default API_URL;
