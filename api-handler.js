// API Configuration
const API_CONFIG = {
    BASE_URL: 'https://your-app.onrender.com', // Your Render URL
    ENDPOINTS: {
        SIGNUP: '/api/signup',
        LOGIN: '/api/login',
        HEALTH: '/api/health'
    }
};

class ApiHandler {
    constructor(baseUrl) {
        this.baseUrl = baseUrl || API_CONFIG.BASE_URL;
    }

    async signup(userData) {
        try {
            const response = await fetch(`${this.baseUrl}${API_CONFIG.ENDPOINTS.SIGNUP}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(userData)
            });
            return await response.json();
        } catch (error) {
            console.error('Signup error:', error);
            return {success: false, message: 'Network error'};
        }
    }

    async login(credentials) {
        try {
            const response = await fetch(`${this.baseUrl}${API_CONFIG.ENDPOINTS.LOGIN}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(credentials)
            });
            return await response.json();
        } catch (error) {
            console.error('Login error:', error);
            return {success: false, message: 'Network error'};
        }
    }
}

// Form Handler
class SignupForm {
    constructor() {
        this.form = document.getElementById('signupForm');
        if (this.form) this.init();
    }

    init() {
        this.form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleSubmit(e);
        });
    }

    async handleSubmit(event) {
        const button = event.target.querySelector('button[type="submit"]');
        const originalText = button.innerHTML;
        
        // Disable button
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';

        // Get form data
        const userData = {
            email: document.getElementById('email').value,
            phone: document.getElementById('phone').value,
            password: document.getElementById('password').value
        };

        // Validate
        if (!this.validateForm(userData)) {
            button.disabled = false;
            button.innerHTML = originalText;
            return;
        }

        // Call API
        const api = new ApiHandler();
        const result = await api.signup(userData);

        if (result.success) {
            alert('Account created!');
            // Store user data
            localStorage.setItem('user', JSON.stringify(result.user));
            // Redirect
            window.location.href = 'dashboard.html';
        } else {
            alert(result.message || 'Signup failed');
        }

        // Reset button
        button.disabled = false;
        button.innerHTML = originalText;
    }

    validateForm(data) {
        if (!data.email.includes('@')) {
            alert('Invalid email');
            return false;
        }
        if (data.password.length < 8) {
            alert('Password must be at least 8 characters');
            return false;
        }
        return true;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    new SignupForm();
});

