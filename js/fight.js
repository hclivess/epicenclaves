// DOM elements
const battleLog = document.getElementById('battleLog');
const playerHealth = document.getElementById('playerHealth');
const enemyHealth = document.getElementById('enemyHealth');
const playerHpDisplay = document.getElementById('playerHpDisplay');
const enemyHpDisplay = document.getElementById('enemyHpDisplay');
const skipButton = document.getElementById('skipAnimation');
const playerPicture = document.querySelector('.player');
const enemyPicture = document.querySelector('.enemy');

let currentRoundIndex = 0;
let isAnimationSkipped = false;
let isBattleOver = false;

// New variables to track current HP
let currentPlayerHp;
let currentEnemyHp;

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
            .to(attacker, {x: attacker.classList.contains('player') ? 50 : -50, duration: 0.2})
            .to(attacker, {x: 0, duration: 0.2})
            .to(target, {x: target.classList.contains('player') ? -25 : 25, duration: 0.1}, "-=0.2")
            .to(target, {x: 0, duration: 0.1});
    });
}

function animateProfilePicture(pictureElement, isDamageTaken) {
    return new Promise((resolve) => {
        const tl = gsap.timeline({onComplete: resolve});
        if (isDamageTaken) {
            tl.to(pictureElement, {scale: 1.2, duration: 0.1})
              .to(pictureElement, {scale: 1, duration: 0.1});
        } else {
            tl.to(pictureElement, {x: 10, duration: 0.1})
              .to(pictureElement, {x: 0, duration: 0.1});
        }
    });
}

function addLogMessage(message, className) {
    const li = document.createElement('li');
    li.textContent = message;
    li.classList.add('battle-message');

    switch(className) {
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
        case 'armor':
        case 'armor_break':
        case 'armor_miss':
        case 'no_armor':
            li.classList.add('armor-message');
            break;
        case 'attack':
            if (message.toLowerCase().startsWith('you')) {
                li.classList.add('player-attack');
            } else {
                li.classList.add('enemy-attack');
            }
            break;
        default:
            li.classList.add('general-message');
    }

    battleLog.insertBefore(li, battleLog.firstChild);
    requestAnimationFrame(() => {
        battleLog.scrollTop = 0;
    });
}

function skipAnimation() {
    isAnimationSkipped = true;
    gsap.globalTimeline.timeScale(10);
    skipButton.disabled = true;
}

async function processAction(action) {
    addLogMessage(action.message, action.type);

    if (action.type === 'attack') {
        if (action.actor === 'player') {
            currentEnemyHp -= action.damage;
            showDamagePopUp(action.damage, false);
            if (!isAnimationSkipped) await animateAttack(playerPicture, enemyPicture);
            await animateProfilePicture(enemyPicture, true);
            updateHealth(currentEnemyHp, battleData.enemy.max_hp, enemyHealth, enemyHpDisplay);
        } else {
            currentPlayerHp -= action.damage;
            showDamagePopUp(action.damage, true);
            if (!isAnimationSkipped) await animateAttack(enemyPicture, playerPicture);
            await animateProfilePicture(playerPicture, true);
            updateHealth(currentPlayerHp, battleData.player.max_hp, playerHealth, playerHpDisplay);
        }
    }

    if (!isAnimationSkipped) {
        await new Promise(resolve => setTimeout(resolve, 500));
    } else {
        await new Promise(resolve => setTimeout(resolve, 50));
    }
}

async function processRound(roundData) {
    // Add the round message
    addLogMessage(roundData.message, 'round-message');

    // Process actions if they exist
    if (roundData.actions && roundData.actions.length > 0) {
        for (const action of roundData.actions) {
            await processAction(action);
        }
    }

    // Update health after each round
    currentPlayerHp = roundData.player_hp;
    currentEnemyHp = roundData.enemy_hp;
    updateHealth(currentPlayerHp, battleData.player.max_hp, playerHealth, playerHpDisplay);
    updateHealth(currentEnemyHp, battleData.enemy.max_hp, enemyHealth, enemyHpDisplay);
}

async function startBattle() {
    console.log("Starting battle with data:", battleData);  // Debug log

    // Initialize current HP with the starting values
    currentPlayerHp = battleData.player.current_hp;
    currentEnemyHp = battleData.enemy.current_hp;

    // Update initial health displays
    updateHealth(currentPlayerHp, battleData.player.max_hp, playerHealth, playerHpDisplay);
    updateHealth(currentEnemyHp, battleData.enemy.max_hp, enemyHealth, enemyHpDisplay);

    // Process all rounds
    for (let i = 0; i < battleData.rounds.length; i++) {
        console.log(`Processing round ${i}`);  // Debug log
        await processRound(battleData.rounds[i]);
        if (isAnimationSkipped) {
            await new Promise(resolve => setTimeout(resolve, 50));
        } else {
            await new Promise(resolve => setTimeout(resolve, 500));
        }
    }

    console.log("Battle ended");  // Debug log
    skipButton.disabled = true;
}

window.onload = function () {
    console.log("Window loaded, starting battle");  // Debug log
    startBattle();
    skipButton.addEventListener('click', skipAnimation);
};