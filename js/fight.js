// DOM elements
const battleLog = document.getElementById('battleLog');
const playerHealth = document.getElementById('playerHealth');
const enemyHealth = document.getElementById('enemyHealth');
const playerHpDisplay = document.getElementById('playerHpDisplay');
const enemyHpDisplay = document.getElementById('enemyHpDisplay');
const skipButton = document.getElementById('skipAnimation');

let currentRoundIndex = 0;
let isAnimationSkipped = false;

function updateHealth(health, maxHealth, healthElement, hpDisplayElement) {
    const healthPercentage = Math.max(0, Math.min((health / maxHealth) * 100, 100));
    healthElement.style.width = `${healthPercentage}%`;
    hpDisplayElement.textContent = `${Math.max(0, health)} / ${maxHealth} HP`;
}

function showDamagePopUp(damage, isPlayer) {
    if (damage <= 0) return;
    const popUpContainer = document.querySelector(isPlayer ? '.player-pop-up' : '.enemy-pop-up');
    const popUp = document.createElement('div');
    popUp.className = 'pop-up';
    popUp.textContent = damage;
    popUpContainer.appendChild(popUp);

    gsap.to(popUp, {
        y: -50,
        opacity: 0,
        duration: 1,
        onComplete: () => popUpContainer.removeChild(popUp)
    });
}

function animateAttack(attacker, target) {
    return new Promise((resolve) => {
        gsap.timeline({onComplete: resolve})
            .to(attacker, {x: attacker === playerHealth.parentElement ? 50 : -50, duration: 0.2})
            .to(attacker, {x: 0, duration: 0.2})
            .to(target, {x: target === playerHealth.parentElement ? -25 : 25, duration: 0.1}, "-=0.2")
            .to(target, {x: 0, duration: 0.1});
    });
}

async function processAction(action, playerHp, enemyHp) {
    const li = document.createElement('li');
    li.textContent = action.message;

    switch (action.type) {
        case 'attack':
            if (action.actor === 'player') {
                li.classList.add('player-attack');
                showDamagePopUp(action.damage, false);
                await animateAttack(playerHealth.parentElement, enemyHealth.parentElement);
                updateHealth(enemyHp, battleData.enemy.max_hp, enemyHealth, enemyHpDisplay);
            } else {
                li.classList.add('enemy-attack');
                showDamagePopUp(action.damage, true);
                await animateAttack(enemyHealth.parentElement, playerHealth.parentElement);
                updateHealth(playerHp, battleData.player.max_hp, playerHealth, playerHpDisplay);
            }
            break;
        case 'armor':
        case 'armor_break':
        case 'armor_miss':
        case 'no_armor':
            li.classList.add('armor-message');
            break;
        case 'defeat':
            li.classList.add('defeat-message');
            break;
        case 'escape':
            li.classList.add('escape-message');
            break;
        case 'loot':
            li.classList.add('loot-message');
            break;
        case 'no_loot':
            li.classList.add('no-loot-message');
            break;
        case 'exp_gain':
            li.classList.add('exp-gain-message');
            break;
    }

    battleLog.appendChild(li);
    battleLog.scrollTop = battleLog.scrollHeight;

    // Add a small delay between actions for readability
    await new Promise(resolve => setTimeout(resolve, 500));
}

async function processRound(roundData) {
    for (const action of roundData.actions) {
        await processAction(action, roundData.player_hp, roundData.enemy_hp);
    }
}

function skipAnimation() {
    isAnimationSkipped = true;
    currentRoundIndex = battleData.rounds.length - 1;
    const finalRound = battleData.rounds[currentRoundIndex];
    updateHealth(finalRound.player_hp, battleData.player.max_hp, playerHealth, playerHpDisplay);
    updateHealth(finalRound.enemy_hp, battleData.enemy.max_hp, enemyHealth, enemyHpDisplay);
    battleData.rounds.forEach(round => {
        round.actions.forEach(action => {
            const li = document.createElement('li');
            li.textContent = action.message;
            battleLog.appendChild(li);
        });
    });
    battleLog.scrollTop = battleLog.scrollHeight;
    skipButton.disabled = true;
}

async function startBattle() {
    updateHealth(battleData.player.current_hp, battleData.player.max_hp, playerHealth, playerHpDisplay);
    updateHealth(battleData.enemy.current_hp, battleData.enemy.max_hp, enemyHealth, enemyHpDisplay);

    async function processNextRound() {
        if (isAnimationSkipped) return;

        if (currentRoundIndex < battleData.rounds.length) {
            const roundData = battleData.rounds[currentRoundIndex];
            await processRound(roundData);
            currentRoundIndex++;
            setTimeout(processNextRound, 1000);
        } else {
            skipButton.disabled = true;
        }
    }

    processNextRound();
}

window.onload = function () {
    startBattle();
    skipButton.addEventListener('click', skipAnimation);
};