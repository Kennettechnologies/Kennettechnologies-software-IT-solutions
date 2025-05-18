const config = {
    API_BASE_URL: process.env.API_BASE_URL || 'http://13.250.108.137:8000',
    ENDPOINTS: {
        PRODUCT: '/product/product',
        USER: '/customer/user',
        AUTH_USER: '/customer/auser',
        AUTH_EMPLOYEE: '/employee/aemployee',
        BOOKING: '/booking',
        PAYMENT: '/payment',
        HANDLE_ORDERS: '/handleorders',
        PRODUCT_PROGRESS: '/handleorders/productprogress',
        VIEW_ORDERS: '/handleorders/vieworders'
    },
    AUTH: {
        TOKEN_KEY: 'auth_token',
        USER_KEY: 'username'
    },
    ERROR_MESSAGES: {
        NETWORK_ERROR: 'Network error occurred. Please check your connection.',
        AUTH_ERROR: 'Authentication failed. Please check your credentials.',
        SERVER_ERROR: 'Server error occurred. Please try again later.',
        INVALID_INPUT: 'Invalid input provided. Please check your input.'
    }
};

// Helper functions for API calls
const apiHelper = {
    async fetchWithAuth(url, options = {}) {
        const token = sessionStorage.getItem(config.AUTH.TOKEN_KEY);
        const headers = {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
            ...options.headers
        };

        try {
            const response = await fetch(url, { ...options, headers });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    },

    handleError(error) {
        if (error.message.includes('NetworkError')) {
            return config.ERROR_MESSAGES.NETWORK_ERROR;
        }
        return error.message || config.ERROR_MESSAGES.SERVER_ERROR;
    }
};

// Export both config and helper
window.config = config;
window.apiHelper = apiHelper; 