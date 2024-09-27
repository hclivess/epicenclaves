// DOM elements
const battleLog = document.getElementById('battleLog');
const playerHealth = document.getElementById('playerHealth');
const enemyHealth = document.getElementById('enemyHealth');
const playerHpDisplay = document.getElementById('playerHpDisplay');
const enemyHpDisplay = document.getElementById('enemyHpDisplay');
const playerMana = document.getElementById('playerMana');
const playerManaDisplay = document.getElementById('playerManaDisplay');
const skipButton = document.getElementById('skipAnimation');
const playerPicture = document.querySelector('.player');
const enemyPicture = document.querySelector('.enemy');

let currentRoundIndex = 0;
let isAnimationSkipped = false;
let isBattleOver = false;

// Variables to track current HP and Mana
let currentPlayerHp;
let currentEnemyHp;
let currentPlayerMana;

function updateHealthAndMana(health, maxHealth, mana, maxMana, healthElement, hpDisplayElement, manaElement, manaDisplayElement) {
    const healthPercentage = Math.max(0, Math.min((health / maxHealth) * 100, 100));
    healthElement.style.width = `${healthPercentage}%`;
    hpDisplayElement.textContent = `${Math.max(0, health)} / ${maxHealth} HP`;

    if (manaElement && manaDisplayElement) {
        const manaPercentage = Math.max(0, Math.min((mana / maxMana) * 100, 100));
        manaElement.style.width = `${manaPercentage}%`;
        manaDisplayElement.textContent = `${Math.max(0, mana)} / ${maxMana} Mana`;
    }
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
    if (!message || message.trim() === '') {
        return;
    }

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
            currentEnemyHp = action.final_enemy_hp !== undefined ? action.final_enemy_hp : currentEnemyHp - action.damage;
            showDamagePopUp(action.damage, false);
            if (!isAnimationSkipped) await animateAttack(playerPicture, enemyPicture);
            await animateProfilePicture(enemyPicture, true);
        } else {
            currentPlayerHp = action.final_hp !== undefined ? action.final_hp : currentPlayerHp - action.damage;
            showDamagePopUp(action.damage, true);
            if (!isAnimationSkipped) await animateAttack(enemyPicture, playerPicture);
            await animateProfilePicture(playerPicture, true);
        }
    } else if (action.type === 'spell') {
        if (action.mana_used) {
            currentPlayerMana -= action.mana_used;
        }
        if (action.healing_done) {
            currentPlayerHp = action.final_player_hp !== undefined ? action.final_player_hp : Math.min(currentPlayerHp + action.healing_done, battleData.player.max_hp);
            showDamagePopUp(action.healing_done, true);
            await animateProfilePicture(playerPicture, false);
        }
        if (action.damage_dealt) {
            currentEnemyHp = action.final_enemy_hp !== undefined ? action.final_enemy_hp : currentEnemyHp - action.damage_dealt;
            showDamagePopUp(action.damage_dealt, false);
            if (!isAnimationSkipped) await animateAttack(playerPicture, enemyPicture);
            await animateProfilePicture(enemyPicture, true);
        }
    }

    updateHealthAndMana(
        currentPlayerHp, battleData.player.max_hp,
        currentPlayerMana, battleData.player.max_mana,
        playerHealth, playerHpDisplay,
        playerMana, playerManaDisplay
    );
    updateHealthAndMana(currentEnemyHp, battleData.enemy.max_hp, null, null, enemyHealth, enemyHpDisplay);

    if (!isAnimationSkipped) {
        await new Promise(resolve => setTimeout(resolve, 500));
    } else {
        await new Promise(resolve => setTimeout(resolve, 50));
    }
}

async function processRound(roundData) {
    addLogMessage(roundData.message, 'round-message');

    if (roundData.actions && roundData.actions.length > 0) {
        for (const action of roundData.actions) {
            await processAction(action);
        }
    }

    currentPlayerHp = roundData.player_hp;
    currentEnemyHp = roundData.enemy_hp;
    currentPlayerMana = roundData.player_mana;
    updateHealthAndMana(
        currentPlayerHp, battleData.player.max_hp,
        currentPlayerMana, battleData.player.max_mana,
        playerHealth, playerHpDisplay,
        playerMana, playerManaDisplay
    );
    updateHealthAndMana(currentEnemyHp, battleData.enemy.max_hp, null, null, enemyHealth, enemyHpDisplay);
}

async function startBattle() {
    console.log("Starting battle with data:", battleData);

    currentPlayerHp = battleData.player.current_hp;
    currentEnemyHp = battleData.enemy.current_hp;
    currentPlayerMana = battleData.player.current_mana;

    updateHealthAndMana(
        currentPlayerHp, battleData.player.max_hp,
        currentPlayerMana, battleData.player.max_mana,
        playerHealth, playerHpDisplay,
        playerMana, playerManaDisplay
    );
    updateHealthAndMana(currentEnemyHp, battleData.enemy.max_hp, null, null, enemyHealth, enemyHpDisplay);

    for (let i = 0; i < battleData.rounds.length; i++) {
        console.log(`Processing round ${i}`);
        await processRound(battleData.rounds[i]);
        if (isAnimationSkipped) {
            await new Promise(resolve => setTimeout(resolve, 50));
        } else {
            await new Promise(resolve => setTimeout(resolve, 500));
        }
    }

    console.log("Battle ended");
    skipButton.disabled = true;
}

window.onload = function () {
    console.log("Window loaded, starting battle");
    startBattle();
    skipButton.addEventListener('click', skipAnimation);
};