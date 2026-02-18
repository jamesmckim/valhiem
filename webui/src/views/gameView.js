// webui/scr/views/gameView.js
export class GameView {
    renderGrid(games) {
        const grid = document.querySelector('.game-grid');
		if (!grid) return;
		
        grid.innerHTML = games.map(game => `
            <div class="server-card game-card">
                <div class="card-header">
                    <h2>${game.name}</h2>
                    <span class="status-indicator online" style="background: #ebf5ff; color: #3498db;">Stable</span>
                </div>
                <div class="card-body" style="text-align: center; padding: 20px 0;">
                    <div style="font-size: 3rem; margin-bottom: 10px;">${game.icon}</div>
                    <p><strong>Version:</strong> ${game.version}</p>
                </div>
                <div class="card-controls">
                    <button class="btn-login" data-id="${game.id}">Deploy Server</button>
                </div>
            </div>
        `).join('');
    }
};