// webui/src/controllers/authControllers.js
import Auth from '../services/authService.js';

export class AuthController {
    constructor(startAppCallback) {
        this.loginForm = document.getElementById('login-form');
        this.overlay = document.getElementById('login-overlay');
        this.startApp = startAppCallback;
    }

    init() {
        if (Auth.getToken()) {
            this.startApp();
            return;
        }

        this.loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const u = document.getElementById('username').value;
            const p = document.getElementById('password').value;

            try {
                await Auth.login(u, p);
                this.startApp();
            } catch (err) {
                alert("Unauthorized: Please check your credentials.");
            }
        });
    }

    handleLogout() {
        Auth.logout();
    }

    hideLogin() {
        this.overlay.style.display = 'none';
    }
}