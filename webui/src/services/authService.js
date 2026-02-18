// webui/src/services/authService.js
const Auth = {
    // 1. Storage Helpers
    saveToken(token) {
        localStorage.setItem('craftcloud_token', token);
    },

    getToken() {
        return localStorage.getItem('craftcloud_token');
    },

    logout() {
        localStorage.removeItem('craftcloud_token');
        // Refresh the page so the App Controller shows the login overlay again
        window.location.href = '/';
    },

    // 2. THE LOGIN HANDSHAKE
    async login(username, password) {
        // FastAPI requires 'application/x-www-form-urlencoded' for /token
        const params = new URLSearchParams();
        params.append('username', username);
        params.append('password', password);

        const response = await fetch('/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: params
        });

        if (!response.ok) {
            throw new Error("Invalid username or password");
        }

        const data = await response.json();
        this.saveToken(data.access_token);
        return data;
    },

    // 3. SECURE API CALLER
    async call(endpoint, options = {}) {
        const token = this.getToken();
		
		// If no token, we can't make authorized calls
		if (!token) {
			console.warn("No token found, redirecting to login.");
			window.location.href = '/';
			return;
		}
		
        const headers = {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            ...options.headers
        };

        const response = await fetch(endpoint, { ...options, headers });

        // Auto-logout if the token is expired/invalid
        if (response.status === 401) {
            this.logout();
        }

        return response;
    }
};

export default Auth;