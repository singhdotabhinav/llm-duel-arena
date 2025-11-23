// API Configuration - automatically detects local vs AWS deployment
(function() {
  'use strict';
  
  // Detect if we're running locally or on AWS
  const isLocal = window.location.hostname === 'localhost' || 
                  window.location.hostname === '127.0.0.1' ||
                  window.location.hostname.startsWith('192.168.') ||
                  window.location.hostname.startsWith('10.');
  
  // API base URL
  const API_BASE_URL = isLocal 
    ? 'http://localhost:8000'
    : window.location.origin;  // Use same origin in production (CloudFront -> API Gateway)
  
  // Export configuration
  window.APP_CONFIG = {
    API_BASE_URL: API_BASE_URL,
    IS_LOCAL: isLocal,
    API_PATHS: {
      games: '/api/games',
      auth: '/auth',
      llm: '/api/llm'
    }
  };
  
  // Helper function to build API URLs
  window.getApiUrl = function(path) {
    const cleanPath = path.startsWith('/') ? path : '/' + path;
    
    // Handle auth routes - FastAPI uses /auth but Lambda uses /api/auth
    let normalizedPath = cleanPath;
    if (isLocal && cleanPath.startsWith('/api/auth/')) {
      // Convert /api/auth/* to /auth/* for local FastAPI
      normalizedPath = cleanPath.replace('/api/auth/', '/auth/');
    } else if (!isLocal && cleanPath.startsWith('/auth/')) {
      // Convert /auth/* to /api/auth/* for AWS Lambda
      normalizedPath = cleanPath.replace('/auth/', '/api/auth/');
    }
    
    if (isLocal) {
      return API_BASE_URL + normalizedPath;
    }
    // In production, API Gateway is on a different domain
    // This should be set via environment variable or meta tag
    const apiGatewayUrl = document.querySelector('meta[name="api-gateway-url"]')?.content;
    if (apiGatewayUrl) {
      return apiGatewayUrl + normalizedPath;
    }
    // Fallback: assume API Gateway is on same domain (if using CloudFront -> API Gateway integration)
    return API_BASE_URL + normalizedPath;
  };
  
  console.log('🔧 App Config:', window.APP_CONFIG);
})();




