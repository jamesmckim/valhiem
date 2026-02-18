// webui/src/controllers/dashboardController.js
export class DashboardController {
    constructor(model, view) {
        this.model = model;
        this.view = view;
    }

    async refresh() {
        try {
            // 1. Fetch the list of servers first
            const serverList = await this.model.getAllServers();

            // 2. Fetch details (CPU/RAM) for EACH server in parallel
            // We map over the list and call getServerDetails for every ID
            const detailPromises = serverList.map(server => 
                this.model.getServerDetails(server.id)
            );
            
            // Wait for all details and the user profile to load
            const [serversWithStats, user] = await Promise.all([
                Promise.all(detailPromises),
                this.model.getProfile()
            ]);
            
            // 3. Render the servers WITH the stats
            this.view.renderServers(serversWithStats, this.handleServerAction.bind(this));
            this.updateUserUI(user);
        } catch (err) {
            console.error("Dashboard Sync Error:", err);
        }
    }

    updateUserUI(user) {
        const nameEl = document.getElementById('display-username');
        const creditEl = document.getElementById('display-credits');
        if (nameEl) nameEl.textContent = user.username;
        if (creditEl) creditEl.textContent = user.credits.toFixed(2);
    }

    async handleServerAction(serverId, currentStatus) {
        // UI Feedback logic here (e.g., setting button to 'Processing...')
        try {
            const action = (currentStatus === 'online') ? 'stop' : 'start';
            await this.model.sendPowerAction(serverId, action);
            await this.refresh(); // Refresh after action
        } catch (err) {
            alert(`Action failed: ${err.message}`);
        }
    }

    startHeartbeat(ms = 3000) {
        this.refresh();
        return setInterval(() => this.refresh(), ms);
    }
}