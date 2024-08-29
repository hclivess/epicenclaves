
        const battleLog = document.getElementById('battleLog');
        const playerHealth = document.getElementById('playerHealth');
        const enemyHealth = document.getElementById('enemyHealth');
        const playerHpDisplay = document.getElementById('playerHpDisplay');
        const enemyHpDisplay = document.getElementById('enemyHpDisplay');

        let playerCurrentHealth = battleData.player.max_hp;  // Start with max HP
        let enemyCurrentHealth = battleData.enemy.max_hp;    // Start with max HP
        const playerMaxHealth = battleData.player.max_hp;
        const enemyMaxHealth = battleData.enemy.max_hp;

        let animationInterval;
        let currentRoundIndex = 0;

        function updateHealth(health, maxHealth, healthElement, hpDisplayElement) {
            const clampedHealth = Math.max(0, Math.min(health, maxHealth));
            const healthPercentage = Math.min((clampedHealth / maxHealth) * 100, 100);

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

        function animateAttack(attacker, target) {
            const tl = gsap.timeline();
            tl.to(attacker, { x: attacker.classList.contains('player') ? 100 : -100, duration: 0.2 })
              .to(attacker, { x: 0, duration: 0.2 })
              .to(target, { x: target.classList.contains('player') ? -50 : 50, duration: 0.1 }, "-=0.2")
              .to(target, { x: 0, duration: 0.1 });
        }

        function skipAnimation() {
            clearInterval(animationInterval);

            // Show all battle messages
            battleData.rounds.forEach((roundData) => {
                const li = document.createElement('li');
                li.className = 'list-group-item battle-message';
                li.textContent = roundData.message;

                if (roundData.message.includes("You hit") || roundData.message.includes("You critical hit")) {
                    li.classList.add('player-attack');
                } else if (roundData.message.includes("hit you")) {
                    li.classList.add('enemy-attack');
                } else if (roundData.message.includes("defeated") || roundData.message.includes("escaped")) {
                    li.classList.add('battle-result');
                }

                battleLog.appendChild(li);
            });

            // Update final health
            const finalRound = battleData.rounds[battleData.rounds.length - 1];
            playerCurrentHealth = finalRound.player_hp;
            enemyCurrentHealth = finalRound.enemy_hp;
            updateHealth(playerCurrentHealth, playerMaxHealth, playerHealth, playerHpDisplay);
            updateHealth(enemyCurrentHealth, enemyMaxHealth, enemyHealth, enemyHpDisplay);

            // Scroll to the bottom of the battle log container
            const battleLogContainer = document.querySelector('.battle-log-container');
            battleLogContainer.scrollTop = battleLogContainer.scrollHeight;

            // Disable the skip button
            document.getElementById('skipAnimation').disabled = true;
        }

        function startBattle() {
            // Initialize health displays
            updateHealth(playerCurrentHealth, playerMaxHealth, playerHealth, playerHpDisplay);
            updateHealth(enemyCurrentHealth, enemyMaxHealth, enemyHealth, enemyHpDisplay);

            animationInterval = setInterval(() => {
                if (currentRoundIndex < battleData.rounds.length) {
                    const roundData = battleData.rounds[currentRoundIndex];

                    const li = document.createElement('li');
                    li.className = 'list-group-item battle-message';
                    li.textContent = roundData.message;

                    if (roundData.message.includes("You hit") || roundData.message.includes("You critical hit")) {
                        li.classList.add('player-attack');
                        const damage = Math.abs(roundData.enemy_hp - enemyCurrentHealth);
                        showDamagePopUp(damage, false, roundData.message.includes("critical hit"));
                        animateAttack(document.querySelector('.player'), document.querySelector('.enemy'));
                        enemyCurrentHealth = roundData.enemy_hp;
                        updateHealth(enemyCurrentHealth, enemyMaxHealth, enemyHealth, enemyHpDisplay);
                    } else if (roundData.message.includes("hit you")) {
                        li.classList.add('enemy-attack');
                        const damage = Math.abs(roundData.player_hp - playerCurrentHealth);
                        showDamagePopUp(damage, true);
                        animateAttack(document.querySelector('.enemy'), document.querySelector('.player'));
                        playerCurrentHealth = roundData.player_hp;
                        updateHealth(playerCurrentHealth, playerMaxHealth, playerHealth, playerHpDisplay);
                    } else if (roundData.message.includes("defeated") || roundData.message.includes("escaped")) {
                        li.classList.add('battle-result');
                    }

                    battleLog.appendChild(li);

                    // Scroll to the bottom of the battle log container
                    const battleLogContainer = document.querySelector('.battle-log-container');
                    battleLogContainer.scrollTop = battleLogContainer.scrollHeight;

                    currentRoundIndex++;
                } else {
                    clearInterval(animationInterval);
                    document.getElementById('skipAnimation').disabled = true;
                }
            }, 1000);  // Delay each message by 1 second
        }

        window.onload = function () {
            startBattle();
            document.getElementById('skipAnimation').addEventListener('click', skipAnimation);
        };
