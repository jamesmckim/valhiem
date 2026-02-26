// webui/src/controllers/dashboardController.js
export class DashboardController {
    constructor(model, view, navView) {
        this.model = model;
        this.view = view;
		this.navView = navView;
    }

    async refresh() {
        try {
            // FIRE BOTH REQUESTS AT THE SAME TIME
            // This prevents a server-list crash from stopping the profile fetch!
            const [serverList, user] = await Promise.all([
				this.model.getAllServers().catch(() => []), // Fallback to empty array if fails
				this.model.getProfile()
            ]);
			
			this.updateUserUI(user);
			
            // Fetch details for EACH server
            if (serverList.length > 0) {
                const detailPromises = serverList.map(server => 
                    this.model.getServerDetails(server.id)
                );
                const serversWithStats = await Promise.all(detailPromises);
                
                // Render the grid
                this.view.renderServers(serversWithStats, this.handleServerAction.bind(this));
            } else {
                // Render an empty grid or "No servers" message
                this.view.renderServers([], this.handleServerAction.bind(this));
            }

        } catch (err) {
            console.error("Dashboard Sync Error:", err);
        }
    }

    updateUserUI(user) {
        if (this.navView) {
			this.navView.updateAccountInfo(user);
		}
    }

    async handleServerAction(serverId, currentStatus) {
        try {
            const action = (currentStatus === 'online') ? 'stop' : 'start';
            await this.model.sendPowerAction(serverId, action);
            await this.refresh(); 
        } catch (err) {
            alert(`Action failed: ${err.message}`);
        }
    }

    startHeartbeat(ms = 3000) {
        this.refresh();
        return setInterval(() => this.refresh(), ms);
    }
}