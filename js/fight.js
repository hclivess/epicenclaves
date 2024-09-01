// DOM elements
const battleLog = document.getElementById('battleLog');
const playerHealth = document.getElementById('playerHealth');
const enemyHealth = document.getElementById('enemyHealth');
const playerHpDisplay = document.getElementById('playerHpDisplay');
const enemyHpDisplay = document.getElementById('enemyHpDisplay');
const skipButton = document.getElementById('skipAnimation');

let currentRoundIndex = 0;
let isAnimationSkipped = false;
let isBattleOver = false;

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

function addLogMessage(message, className) {
    const li = document.createElement('li');
    li.textContent = message;
    li.classList.add(className);
    battleLog.appendChild(li);
    battleLog.scrollTop = battleLog.scrollHeight;
}

async function processAction(action, playerHp, enemyHp) {
    if (isBattleOver) return;

    addLogMessage(action.message, action.type);

    if (action.type === 'attack') {
        if (action.actor === 'player') {
            showDamagePopUp(action.damage, false);
            if (!isAnimationSkipped) await animateAttack(playerHealth.parentElement, enemyHealth.parentElement);
            updateHealth(enemyHp, battleData.enemy.max_hp, enemyHealth, enemyHpDisplay);
        } else {
            showDamagePopUp(action.damage, true);
            if (!isAnimationSkipped) await animateAttack(enemyHealth.parentElement, playerHealth.parentElement);
            updateHealth(playerHp, battleData.player.max_hp, playerHealth, playerHpDisplay);
        }
    }

    if (action.type === 'defeat' || action.type === 'escape') {
        isBattleOver = true;
    }

    if (!isAnimationSkipped) {
        await new Promise(resolve => setTimeout(resolve, 500));
    }
}

async function processRound(roundData) {
    for (const action of roundData.actions) {
        await processAction(action, roundData.player_hp, roundData.enemy_hp);
        if (isBattleOver) break;
    }
}

function skipAnimation() {
    isAnimationSkipped = true;
    battleLog.innerHTML = ''; // Clear the battle log before repopulating

    battleData.rounds.forEach((round) => {
        round.actions.forEach((action) => {
            addLogMessage(action.message, action.type);
            if (action.type === 'defeat' || action.type === 'escape') {
                isBattleOver = true;
            }
        });
        if (isBattleOver) return;
    });

    // Update health displays to final values
    const finalRound = battleData.rounds[battleData.rounds.length - 1];
    updateHealth(finalRound.player_hp, battleData.player.max_hp, playerHealth, playerHpDisplay);
    updateHealth(finalRound.enemy_hp, battleData.enemy.max_hp, enemyHealth, enemyHpDisplay);

    battleLog.scrollTop = battleLog.scrollHeight;
    skipButton.disabled = true;
}

async function startBattle() {
    updateHealth(battleData.player.current_hp, battleData.player.max_hp, playerHealth, playerHpDisplay);
    updateHealth(battleData.enemy.current_hp, battleData.enemy.max_hp, enemyHealth, enemyHpDisplay);

    async function processNextRound() {
        if (isAnimationSkipped || isBattleOver) return;

        if (currentRoundIndex < battleData.rounds.length) {
            const roundData = battleData.rounds[currentRoundIndex];
            await processRound(roundData);
            currentRoundIndex++;
            if (!isBattleOver) {
                setTimeout(processNextRound, 1000);
            }
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