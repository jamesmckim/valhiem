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
			this.bindLogout();
            return;
        }

        this.loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const u = document.getElementById('username').value;
            const p = document.getElementById('password').value;

            try {
                await Auth.login(u, p);
                this.startApp();
				this.bindLogout();
            } catch (err) {
                alert("Unauthorized: Please check your credentials.");
            }
        });
    }
	
	bindLogout() {
        const btn = document.getElementById('logout-btn');
        
        if (!btn) return;
		
		btn.removeEventListener('click', this.handleLogout);
        btn.addEventListener('click', this.handleLogout);
	}

    handleLogout = () => {
        Auth.logout();
    }

    hideLogin() {
        this.overlay.style.display = 'none';
    }
}