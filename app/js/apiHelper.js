const apiHelper = {
    async fetchWithAuth(url, options = {}) {
        // Add authentication headers if needed in the future
        const fetchOptions = {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...(options.headers || {})
            }
        };
        const response = await fetch(url, fetchOptions);
        if (!response.ok) {
            // Try to parse error message from server
            let errorMsg = "Network response was not ok.";
            try {
                const errorData = await response.json();
                errorMsg = errorData.message || errorMsg;
            } catch (e) {}
            throw new Error(errorMsg);
        }
        return response.json();
    },
    handleError(error) {
        return error && error.message ? error.message : "An unknown error occurred.";
    }
};