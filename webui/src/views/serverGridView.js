// webui/src/views/serverGridView.js
export class ServerGridView {
    constructor() {
        this.grid = document.getElementById('server-grid');
    }

    renderServers(servers, onAction) {
        this.grid.innerHTML = '';

        servers.forEach(server => {
            const isActive = server.status === 'online';
            const card = document.createElement('section');
            
			card.className = 'server-card';
			card.dataset.serverId = server.id; // Store ID for reference
            
			card.innerHTML = `
				<div class="card-header">
					<h2>${server.name}</h2>
					<span class="status-indicator ${server.status}"></span>
				</div>
				<div class="card-body">
					<div class="stat-group">
						<label>Players Online: <strong>${isActive ? server.players : 0}</strong></label>
					</div>

					<div class="stat-group">
						<label>CPU: ${isActive ? server.cpu.toFixed(1) + '%' : 'N/A'}</label>
						<div class="progress-bar"><div style="width: ${server.cpu}%"></div></div>
					</div>
					<div class="stat-group">
						<label>RAM: ${isActive ? server.ram.toFixed(1) + '%' : 'N/A'}</label>
						<div class="progress-bar"><div style="width: ${server.ram}%" class="ram-fill"></div></div>
					</div>
				</div>
				<div class="card-controls">
                    <button class="action-btn ${isActive ? 'btn-stop' : 'btn-start'}">
                        ${isActive ? 'Stop' : 'Start'}
                    </button>
                    <button class="btn-settings">Settings</button>
                </div>
			`;

            // Attach listener via the passed 'onAction' handler
           const actionBtn = card.querySelector('.action-btn');
        
			// Use the handler passed from the controller
			actionBtn.addEventListener('click', () => {
				onAction(server.id, server.status);
			});

            this.grid.appendChild(card);
        });
    }
}