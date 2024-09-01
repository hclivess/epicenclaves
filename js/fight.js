// DOM elements
const battleLog = document.getElementById('battleLog');
const playerHealth = document.getElementById('playerHealth');
const enemyHealth = document.getElementById('enemyHealth');
const playerHpDisplay = document.getElementById('playerHpDisplay');
const enemyHpDisplay = document.getElementById('enemyHpDisplay');
const skipButton = document.getElementById('skipAnimation');

// Battle state
let playerCurrentHealth, enemyCurrentHealth;
const playerMaxHealth = battleData.player.max_hp;
const enemyMaxHealth = battleData.enemy.max_hp;

let animationInterval;
let currentRoundIndex = 0;
let isAnimationSkipped = false;

// Update health bar and display
function updateHealth(health, maxHealth, healthElement, hpDisplayElement) {
    const clampedHealth = Math.max(0, Math.min(health, maxHealth));
    const healthPercentage = (clampedHealth / maxHealth) * 100;

    healthElement.style.transition = "width 0.3s ease-in-out";
    healthElement.style.width = `${healthPercentage}%`;
    hpDisplayElement.textContent = `${clampedHealth} / ${maxHealth} HP`;

    if (clampedHealth <= 0) {
        healthElement.style.backgroundColor = "red";
        healthElement.style.borderColor = "black";
    } else {
        healthElement.style.backgroundColor = "green";
        healthElement.style.borderColor = "";
    }
}

// Show damage pop-up
function showDamagePopUp(damage, isPlayer, crit = false) {
    const popUpContainer = document.querySelector(isPlayer ? '.player-pop-up' : '.enemy-pop-up');
    const popUp = document.createElement('div');
    popUp.className = 'pop-up';
    popUp.textContent = crit ? `${damage} (CRIT!)` : `${damage}`;

    popUpContainer.appendChild(popUp);

    gsap.fromTo(popUp, {
        y: 0,
        opacity: 1,
        scale: 1,
        color: crit ? 'orange' : undefined
    }, {
        y: -50,
        opacity: 0,
        scale: 1.5,
        duration: 1,
        ease: "power2.out",
        onComplete: () => {
            popUpContainer.removeChild(popUp);
        }
    });
}

// Animate attack
function animateAttack(attacker, target) {
    return new Promise((resolve) => {
        const tl = gsap.timeline({onComplete: resolve});
        tl.to(attacker, { x: attacker.classList.contains('player') ? 100 : -100, duration: 0.2 })
          .to(attacker, { x: 0, duration: 0.2 })
          .to(target, { x: target.classList.contains('player') ? -50 : 50, duration: 0.1 }, "-=0.2")
          .to(target, { x: 0, duration: 0.1 });
    });
}

// Process a single round
async function processRound(roundData, previousPlayerHp, previousEnemyHp) {
    const li = document.createElement('li');
    li.className = 'list-group-item battle-message';
    li.textContent = roundData.message;

    if (roundData.message.includes("You hit") || roundData.message.includes("You critical hit")) {
        li.classList.add('player-attack');
        const damage = previousEnemyHp - roundData.enemy_hp;
        showDamagePopUp(damage, false, roundData.message.includes("critical hit"));
        await animateAttack(document.querySelector('.player'), document.querySelector('.enemy'));
        enemyCurrentHealth = roundData.enemy_hp;
        updateHealth(enemyCurrentHealth, enemyMaxHealth, enemyHealth, enemyHpDisplay);
    } else if (roundData.message.includes("hit you")) {
        li.classList.add('enemy-attack');
        const damage = previousPlayerHp - roundData.player_hp;
        showDamagePopUp(damage, true);
        await animateAttack(document.querySelector('.enemy'), document.querySelector('.player'));
        playerCurrentHealth = roundData.player_hp;
        updateHealth(playerCurrentHealth, playerMaxHealth, playerHealth, playerHpDisplay);
    } else if (roundData.message.includes("defeated") || roundData.message.includes("escaped")) {
        li.classList.add('battle-result');
    }

    battleLog.appendChild(li);

    const battleLogContainer = document.querySelector('.battle-log-container');
    battleLogContainer.scrollTop = battleLogContainer.scrollHeight;
}

// Skip animation
function skipAnimation() {
    isAnimationSkipped = true;
    clearInterval(animationInterval);

    let prevPlayerHp = playerMaxHealth;
    let prevEnemyHp = enemyMaxHealth;

    while (currentRoundIndex < battleData.rounds.length) {
        const roundData = battleData.rounds[currentRoundIndex];
        processRound(roundData, prevPlayerHp, prevEnemyHp);
        prevPlayerHp = roundData.player_hp;
        prevEnemyHp = roundData.enemy_hp;
        currentRoundIndex++;
    }

    skipButton.disabled = true;
}

// Start battle
async function startBattle() {
    // Initialize health with max values
    playerCurrentHealth = playerMaxHealth;
    enemyCurrentHealth = enemyMaxHealth;

    updateHealth(playerCurrentHealth, playerMaxHealth, playerHealth, playerHpDisplay);
    updateHealth(enemyCurrentHealth, enemyMaxHealth, enemyHealth, enemyHpDisplay);

    // Process rounds
    async function processNextRound() {
        if (isAnimationSkipped) return;

        if (currentRoundIndex < battleData.rounds.length) {
            const roundData = battleData.rounds[currentRoundIndex];
            const prevPlayerHp = currentRoundIndex === 0 ? playerMaxHealth : battleData.rounds[currentRoundIndex - 1].player_hp;
            const prevEnemyHp = currentRoundIndex === 0 ? enemyMaxHealth : battleData.rounds[currentRoundIndex - 1].enemy_hp;

            await processRound(roundData, prevPlayerHp, prevEnemyHp);

            playerCurrentHealth = roundData.player_hp;
            enemyCurrentHealth = roundData.enemy_hp;
            currentRoundIndex++;
            setTimeout(processNextRound, 2000);  // 2-second delay between rounds
        } else {
            skipButton.disabled = true;
        }
    }

    // Start processing rounds
    processNextRound();
}

// Initialize
window.onload = function () {
    startBattle();
    skipButton.addEventListener('click', skipAnimation);
};