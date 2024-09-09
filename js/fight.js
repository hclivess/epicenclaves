// DOM elements
const battleLog = document.getElementById('battleLog');
const playerHealth = document.getElementById('playerHealth');
const enemyHealth = document.getElementById('enemyHealth');
const playerHpDisplay = document.getElementById('playerHpDisplay');
const enemyHpDisplay = document.getElementById('enemyHpDisplay');

function updateHealth(health, maxHealth, healthElement, hpDisplayElement) {
    const healthPercentage = Math.max(0, Math.min((health / maxHealth) * 100, 100));
    healthElement.style.width = `${healthPercentage}%`;
    hpDisplayElement.textContent = `${Math.max(0, health)} / ${maxHealth} HP`;
}

function addLogMessage(message, className) {
    const li = document.createElement('li');
    li.textContent = message;
    li.classList.add('battle-message', className);
    battleLog.appendChild(li);
    battleLog.scrollTop = battleLog.scrollHeight;
}

function displayBattleLog() {
    // Clear existing log
    battleLog.innerHTML = '';

    // Display initial battle message
    addLogMessage(battleData.rounds[0].message, 'round-message');

    // Process all rounds
    battleData.rounds.slice(1).forEach((round, index) => {
        addLogMessage(`Round ${index + 1}`, 'round-header');

        // Display round actions
        round.actions.forEach(action => {
            addLogMessage(action.message, action.type);
        });

        // Display round summary
        addLogMessage(round.message, 'round-summary');
    });

    // Update final health display
    updateHealth(battleData.player.current_hp, battleData.player.max_hp, playerHealth, playerHpDisplay);
    updateHealth(battleData.enemy.current_hp, battleData.enemy.max_hp, enemyHealth, enemyHpDisplay);
}

// Start the battle log display when the page loads
window.onload = displayBattleLog;