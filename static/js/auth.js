/**
 * Authentication utility for handling JWT tokens and API requests
 */

class AuthManager {
    constructor() {
        this.token = localStorage.getItem('authToken');
        this.user = JSON.parse(localStorage.getItem('user') || 'null');
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!this.token;
    }

    /**
     * Get current user
     */
    getCurrentUser() {
        return this.user;
    }

    /**
     * Get authentication token
     */
    getToken() {
        return this.token;
    }

    /**
     * Set authentication data
     */
    setAuth(token, user) {
        this.token = token;
        this.user = user;
        localStorage.setItem('authToken', token);
        localStorage.setItem('user', JSON.stringify(user));
    }

    /**
     * Clear authentication data
     */
    clearAuth() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
    }

    /**
     * Make authenticated API request
     */
    async apiRequest(url, options = {}) {
        if (!this.token) {
            throw new Error('No authentication token available');
        }

        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`
            }
        };

        const requestOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, requestOptions);
            
            // Handle token expiration
            if (response.status === 401) {
                this.clearAuth();
                window.location.href = '/login';
                return;
            }

            return response;
        } catch (error) {
            console.error('API request error:', error);
            throw error;
        }
    }

    /**
     * Refresh token
     */
    async refreshToken() {
        try {
            const response = await fetch('/api/refresh', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.setAuth(data.token, this.user);
                return data.token;
            } else {
                this.clearAuth();
                window.location.href = '/login';
                return null;
            }
        } catch (error) {
            console.error('Token refresh error:', error);
            this.clearAuth();
            window.location.href = '/login';
            return null;
        }
    }

    /**
     * Logout user
     */
    logout() {
        this.clearAuth();
        window.location.href = '/login';
    }

    /**
     * Check if user has specific role
     */
    hasRole(role) {
        return this.user && this.user.role === role;
    }

    /**
     * Check if user is admin
     */
    isAdmin() {
        return this.hasRole('admin');
    }
}

// Create global auth manager instance
const authManager = new AuthManager();

// Auto-refresh token before expiration
setInterval(() => {
    if (authManager.isAuthenticated()) {
        // Refresh token every 23 hours (assuming 24-hour expiration)
        authManager.refreshToken();
    }
}, 23 * 60 * 60 * 1000);

// Export for use in other scripts
window.authManager = authManager;

/**
 * Authentication guard and utility functions for the frontend.
 */

(function () {
    // This script should be included in all protected pages.
    // It checks for a valid auth token and redirects to login if it's missing.
    
    const protectedPaths = ['/dashboard', '/chat', '/'];
    const currentPath = window.location.pathname;

    if (protectedPaths.includes(currentPath)) {
        const token = localStorage.getItem('authToken');
        if (!token) {
            // If no token, and we are on a protected page, redirect to login.
            window.location.href = '/login';
            return;
        }

        // Optional: Add token validation logic here to check for expiration
        // For example, by decoding the token (if safe) or making a validation request.
    }
})();

/**
 * A wrapper for the fetch API that automatically adds the JWT Authorization header.
 * @param {string} url - The URL to fetch.
 * @param {object} options - The options for the fetch request (e.g., method, body).
 * @returns {Promise<Response>} The fetch promise.
 */
async function fetchWithAuth(url, options = {}) {
    const token = localStorage.getItem('authToken');

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    return fetch(url, { ...options, headers });
}

/**
 * Logs the user out by removing the token and redirecting to the login page.
 */
function logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    window.location.href = '/login';
}

/**
 * Gets the currently logged-in user's information from localStorage.
 * @returns {object|null} The user object or null if not logged in.
 */
function getCurrentUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
} 