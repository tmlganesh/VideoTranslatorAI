const trimTrailingSlash = (value) => value.replace(/\/+$/, '');

export const getApiBaseUrl = () => {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (envUrl && typeof envUrl === 'string' && envUrl.trim()) {
    return trimTrailingSlash(envUrl.trim());
  }

  if (typeof window === 'undefined') {
    return 'http://localhost:8000';
  }

  const host = window.location.hostname;

  // Local development on same machine.
  if (host === 'localhost' || host === '127.0.0.1') {
    return 'http://localhost:8000';
  }

  // Network access (phone/laptop on LAN) should hit backend on same host.
  return `${window.location.protocol}//${host}:8000`;
};

export const API_BASE_URL = getApiBaseUrl();

export const apiUrl = (path) => {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
};
