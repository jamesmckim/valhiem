// webui/src/controllers/gameController.js
export class GameController {
    constructor(model, view, dashModel) {
        this.model = model;
        this.view = view;
        this.dashModel = dashModel; // Needed to trigger deployment
    }

    async loadGames() {
        try {
            const games = await this.model.fetchAvailableGames();
            this.view.renderGrid(games);
        } catch (err) {
            this.view.showError("Error loading games from CraftCloud.");
        }
    }

    async handleDeploy(gameId, button) {
        button.disabled = true;
        button.textContent = 'Deploying...';

        try {
            await this.dashModel.deployServer(gameId);
            alert(`Success! ${gameId} is spinning up.`);
            button.textContent = 'Active';
            button.style.background = '#2ecc71';
        } catch (err) {
            button.disabled = false;
            button.textContent = 'Deploy Server';
            alert("Deployment failed.");
        }
    }
}