const gridSize = 80;
const verticalTiles = 20;

let horizontalTiles;
let isUserInteracting = false;
let lastInteractionTime = Date.now();
const INTERACTION_COOLDOWN = 2000; // 2 seconds

function calculateHorizontalTiles() {
    const mapContainer = document.querySelector('.map-container');
    horizontalTiles = Math.ceil(mapContainer.offsetWidth / gridSize) + 4;
}

function setUserInteracting(interacting) {
    isUserInteracting = interacting;
    if (interacting) {
        lastInteractionTime = Date.now();
    }
}

function canRefresh() {
    return !isUserInteracting && (Date.now() - lastInteractionTime > INTERACTION_COOLDOWN);
}

function createMap(data) {
    const mapContainer = document.getElementById("map");
    const fragment = document.createDocumentFragment();

    function createTile(x, y) {
        const tile = document.createElement("div");
        tile.className = "tile";
        tile.style.top = y * gridSize + "px";
        tile.style.left = x * gridSize + "px";
        tile.dataset.x = x;
        tile.dataset.y = y;
        fragment.appendChild(tile);
        return tile;
    }

    function createEntityLabel(entity, pos, isPlayer, playerName) {
        const label = document.createElement("div");
        label.className = "entity-label";
        let text = '';
        if (isPlayer) {
            text = `${playerName} Exp:${entity.exp} HP:${entity.hp}`;
        } else {
            text = `${entity.type}`;
            if (entity.level !== undefined) text += ` lvl ${entity.level}`;
            if (entity.control !== undefined) text += ` of ${entity.control}`;
            if (entity.hp !== undefined) text += ` HP: ${entity.hp}`;
        }
        text += ` (${pos.x},${pos.y})`;
        label.textContent = text;
        return label;
    }

    function createEntity(className, x, y, entity, isPlayer = false, playerName = '') {
        const element = document.createElement("div");
        element.className = `entity ${className} ${isPlayer ? 'player' : 'npc'}`;
        element.style.top = y * gridSize + "px";
        element.style.left = x * gridSize + "px";

        if (entity.img) {
            element.style.backgroundImage = `url('${entity.img}')`;
        }

        const label = createEntityLabel(entity, {x: x+1, y: y+1}, isPlayer, playerName);
        element.appendChild(label);

        if (isPlayer) {
            const exclamationMark = document.createElement("div");
            exclamationMark.className = "exclamation-mark";
            exclamationMark.textContent = "!";
            exclamationMark.style.display = "none";
            element.appendChild(exclamationMark);
        }

        if (className === 'outpost') {
            createOutpostRange(x, y);
        }

        fragment.appendChild(element);
        return element;
    }

    function createOutpostRange(x, y) {
        const range = document.createElement("div");
        range.className = "outpost-range";
        const diameter = 21 * gridSize; // 10 tiles on each side, plus the center tile
        range.style.width = `${diameter}px`;
        range.style.height = `${diameter}px`;
        range.style.top = `${(y * gridSize) - (diameter / 2) + (gridSize / 2)}px`;
        range.style.left = `${(x * gridSize) - (diameter / 2) + (gridSize / 2)}px`;
        fragment.appendChild(range);
    }

    function createVisibleTiles() {
        const currentUserData = data.users[currentUser];
        if (currentUserData) {
            const { x_pos, y_pos } = currentUserData;
            const halfWidth = Math.floor(horizontalTiles / 2);
            const halfHeight = Math.floor(verticalTiles / 2);

            for (let y = Math.max(0, y_pos - halfHeight); y < y_pos + halfHeight; y++) {
                for (let x = Math.max(0, x_pos - halfWidth); x < x_pos + halfWidth; x++) {
                    createTile(x, y);
                }
            }
        }
    }

    createVisibleTiles();

    Object.entries(data.users).forEach(([username, user]) => {
        createEntity(user.type.toLowerCase(), user.x_pos - 1, user.y_pos - 1, user, true, username);
    });

    Object.entries(data.construction).forEach(([key, entity]) => {
        const [x, y] = key.split(",").map(Number);
        createEntity(entity.type.toLowerCase(), x - 1, y - 1, {...entity, x_pos: x, y_pos: y}, false);
    });

    mapContainer.appendChild(fragment);
    centerMapOnPlayer();
    checkPlayerPosition();
}

function updateMap(data) {
    const mapContainer = document.getElementById("map");
    mapContainer.innerHTML = '';
    createMap(data);
    checkPlayerPosition();
}

function showDragDirections(targetName) {
    const popup = document.getElementById('popup');
    const directions = ['up', 'down', 'left', 'right'];
    let popupContent = `
        <h3>Drag ${targetName}</h3>
        <p>Choose a direction to drag the player:</p>
    `;
    directions.forEach(direction => {
        popupContent += `<button onclick="performDragAction('${targetName}', '${direction}')">${direction}</button>`;
    });
    popupContent += `<div class="popup-close" onclick="closePopup()">X</div>`;
    popup.innerHTML = popupContent;
}

function updatePopupContent(x_pos, y_pos, tileType) {
    const popup = document.getElementById('popup');
    const currentTile = `${x_pos},${y_pos}`;
    let tileActions = jsonData.actions[currentTile] || [];

    // Check for player actions
    const playersOnTile = Object.values(jsonData.users).filter(user =>
        user.x_pos === x_pos && user.y_pos === y_pos && user !== jsonData.users[currentUser]
    );

    if (playersOnTile.length > 0) {
        playersOnTile.forEach(player => {
            tileActions = tileActions.concat(jsonData.actions[player.name] || []);
        });
    }

    let popupContent = `
        <h3>Tile Information</h3>
        <p>You arrived at ${tileType} (${x_pos}, ${y_pos})</p>
    `;

    if (tileActions.length > 0) {
        tileActions.forEach(action => {
            if (action.action.startsWith('/fight')) {
                const targetName = action.action.split('name=')[1];
                if (action.name === "challenge") {
                    popupContent += `<button onclick="performFightAction('${action.action}&return_to_map=false')">Challenge ${targetName}</button>`;
                } else {
                    // For other fight actions, use the original action name
                    popupContent += `<button onclick="performFightAction('${action.action}&return_to_map=false')">${action.name}</button>`;
                }
            } else if (action.name === "drag") {
                const targetName = action.action.split('target=')[1];
                popupContent += `<button onclick="showDragDirections('${targetName}')">Drag ${targetName}</button>`;
            } else {
                const actionUrl = new URL(action.action, window.location.origin);
                actionUrl.searchParams.append('return_to_map', 'true');
                popupContent += `<button onclick="performAction('${actionUrl}')">${action.name}</button>`;
            }
        });
    } else {
        popupContent += `<p>No actions available for this tile.</p>`;
    }

    popupContent += `<div class="popup-close" onclick="closePopup()">X</div>`;

    popup.innerHTML = popupContent;
    popup.style.display = "block";
}

function checkPlayerPosition() {
    const currentUserData = jsonData.users[currentUser];
    if (currentUserData) {
        const { x_pos, y_pos } = currentUserData;
        const key = `${x_pos},${y_pos}`;
        const entityOnTile = jsonData.construction[key];
        const playersOnTile = Object.entries(jsonData.users).filter(([username, user]) =>
            user.x_pos === x_pos && user.y_pos === y_pos && username !== currentUser
        );

        const playerElement = document.querySelector(`.entity.player[style*="left: ${(x_pos - 1) * gridSize}px"][style*="top: ${(y_pos - 1) * gridSize}px"]`);
        if (playerElement) {
            const exclamationMark = playerElement.querySelector('.exclamation-mark');

            if (entityOnTile || playersOnTile.length > 0 || jsonData.actions[key]) {
                exclamationMark.style.display = "flex";

                if (entityOnTile) {
                    updatePopupContent(x_pos, y_pos, entityOnTile.type);
                } else if (playersOnTile.length > 0) {
                    const [playerUsername, playerData] = playersOnTile[0];
                    updatePopupContent(x_pos, y_pos, playerData.type);
                } else if (jsonData.actions[key]) {
                    updatePopupContent(x_pos, y_pos, 'action');
                }
            } else {
                exclamationMark.style.display = "none";
                closePopup();
            }
        }
    }
}

function performFightAction(actionUrl) {
    setUserInteracting(true);
    window.location.href = actionUrl;
}

function performDragAction(targetName, direction) {
    setUserInteracting(true);
    fetch(`/drag?target=${targetName}&direction=${direction}&return_to_map=true`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            displayMessage(data.message);
        }
        Object.assign(jsonData, data);
        updateMap(jsonData);
        closePopup();
        setUserInteracting(false);
    })
    .catch((error) => {
        console.error('Error:', error);
        displayMessage('An error occurred while dragging the player.');
        setUserInteracting(false);
    });
}

function dragPlayer(targetName, direction) {
    setUserInteracting(true);
    fetch(`/drag?target=${targetName}&direction=${direction}&return_to_map=true`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            displayMessage(data.message);
        }
        updateMap(data);
        closePopup();
        setUserInteracting(false);
    })
    .catch((error) => {
        console.error('Error:', error);
        displayMessage('An error occurred while dragging the player.');
        setUserInteracting(false);
    });
}

function closePopup() {
    const popup = document.getElementById('popup');
    popup.style.display = "none";
}

function movePlayer(direction, steps) {
    setUserInteracting(true);
    isMoving = true;

    function moveStep(remainingSteps) {
        if (remainingSteps > 0) {
            fetch(`/move?direction=${direction}&target=map`)
                .then(response => response.json())
                .then(data => {
                    Object.assign(jsonData, data);
                    updateMap(jsonData);
                    if (data.message) {
                        displayMessage(data.message);
                    }
                    checkPlayerPosition();

                    if (remainingSteps > 1 && !data.message.includes("failed")) {
                        moveStep(remainingSteps - 1);
                    } else {
                        isMoving = false;
                        setUserInteracting(false);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    displayMessage('An error occurred while moving.');
                    isMoving = false;
                    setUserInteracting(false);
                });
        } else {
            isMoving = false;
            setUserInteracting(false);
        }
    }

    moveStep(steps);
}

function moveToPosition(x, y, callback) {
    setUserInteracting(true);
    console.log(`Sending request to move to (${x}, ${y})`);
    fetch(`/move_to?x=${x}&y=${y}&target=map&return_to_map=true`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        console.log('Received response:', data);
        Object.assign(jsonData, data);
        updateMap(jsonData);

        if (data.message) {
            displayMessage(data.message);
        }

        const success = data.x_pos === x && data.y_pos === y;
        callback(success);
        checkPlayerPosition();
        setUserInteracting(false);
    })
    .catch((error) => {
        console.error('Error:', error);
        displayMessage('An error occurred while moving.');
        callback(false);
        setUserInteracting(false);
    });
}

function handleGo() {
    console.log("handleGo function called");

    const x = parseInt(document.getElementById('goto-x').value);
    const y = parseInt(document.getElementById('goto-y').value);
    if (!isNaN(x) && !isNaN(y)) {
        moveToPosition(x, y, (success) => {
            if (success) {
                updateMap(jsonData);
            }
        });
    } else {
        displayMessage('Please enter valid x and y coordinates.');
    }
}

function performAction(actionUrl) {
    setUserInteracting(true);

    // Check if the action is a /temple redirect
    if (actionUrl.includes('/temple')) {
        window.location.href = actionUrl;
        return;
    }

        // Check if the action is a /temple redirect
    if (actionUrl.includes('/alchemist')) {
        window.location.href = actionUrl;
        return;
    }

    fetch(actionUrl)
        .then(response => response.json())
        .then(data => {
            Object.assign(jsonData, data);
            updateMap(jsonData);
            if (data.message) {
                displayMessage(data.message);
            }
            checkPlayerPosition();
            setUserInteracting(false);
        })
        .catch(error => {
            console.error('Error:', error);
            displayMessage('An error occurred while performing the action.');
            setUserInteracting(false);
        });
}

let currentMessage = '';
let messageTimeout = null;
const MESSAGE_DISPLAY_TIME = 5000; // 5 seconds

function displayMessage(message) {
    if (message && message.trim() !== '') {
        currentMessage = message;
        const messageDisplay = document.getElementById('message-display');

        messageDisplay.textContent = message;
        messageDisplay.style.opacity = '1';
        messageDisplay.style.visibility = 'visible';

        // Clear any existing timeout
        if (messageTimeout) {
            clearTimeout(messageTimeout);
        }

        // Set a new timeout
        messageTimeout = setTimeout(() => {
            messageDisplay.style.opacity = '0';
            messageDisplay.style.visibility = 'hidden';
            setTimeout(() => {
                if (messageDisplay.textContent === currentMessage) {
                    messageDisplay.textContent = '';
                    currentMessage = '';
                }
            }, 300); // Short delay for fade-out transition
        }, MESSAGE_DISPLAY_TIME);
    }
}

function addClickListenerToMap() {
    const mapContainer = document.querySelector('.map-container');
    const map = document.getElementById('map');

    mapContainer.addEventListener("click", (event) => {
        const rect = mapContainer.getBoundingClientRect();
        const mapRect = map.getBoundingClientRect();
        const clickX = Math.floor((event.clientX - mapRect.left) / gridSize) + 1;
        const clickY = Math.floor((event.clientY - mapRect.top) / gridSize) + 1;

        console.log(`Clicked on map at (${clickX}, ${clickY})`);
        console.log(`Map container position: left=${rect.left}, top=${rect.top}`);
        console.log(`Map position: left=${mapRect.left}, top=${mapRect.top}`);
        console.log(`Grid size: ${gridSize}`);

        moveToPosition(clickX, clickY, (success) => {
            console.log(`Move to (${clickX}, ${clickY}) ${success ? 'successful' : 'failed'}`);
            if (success) {
                updateMap(jsonData);
            }
        });
    });
}

function centerMapOnPlayer() {
    const currentUserData = jsonData.users[currentUser];
    if (currentUserData) {
        const { x_pos, y_pos } = currentUserData;
        const mapContainer = document.querySelector('.map-container');
        const map = document.getElementById('map');

        const containerWidth = mapContainer.offsetWidth;
        const containerHeight = mapContainer.offsetHeight;

        const leftOffset = (x_pos - 1) * gridSize - (containerWidth / 2) + (gridSize / 2);
        const topOffset = (y_pos - 1) * gridSize - (containerHeight / 2) + (gridSize / 2);

        map.style.left = `${-leftOffset}px`;
        map.style.top = `${-topOffset}px`;
    }
}

function buildPalisade() {
    setUserInteracting(true);
    fetch('/build?entity=palisade&name=town1&return_to_map=true', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            displayMessage(data.message);
        }
        Object.assign(jsonData, data);
        updateMap(jsonData);
        checkPlayerPosition();
        setUserInteracting(false);
    })
    .catch((error) => {
        console.error('Error:', error);
        displayMessage('An error occurred while building the palisade.');
        setUserInteracting(false);
    });
}

function refreshMapData() {
    if (!canRefresh()) {
        return;
    }

    fetch('/map?format=json')
        .then(response => response.json())
        .then(data => {
            const oldPosition = jsonData.users[currentUser];
            Object.assign(jsonData, data);
            updateMap(jsonData);

            // Only check player position and show popup if the player hasn't moved
            const newPosition = jsonData.users[currentUser];
            if (oldPosition.x_pos === newPosition.x_pos && oldPosition.y_pos === newPosition.y_pos) {
                checkPlayerPosition();
            } else {
                closePopup(); // Close popup if player has moved
            }

            // Only display a new message if there isn't already one being shown
            if (data.message && data.message !== currentMessage) {
                displayMessage(data.message);
            }
        })
        .catch(error => {
            console.error('Error refreshing map data:', error);
        });
}

window.addEventListener('resize', () => {
    calculateHorizontalTiles();
    updateMap(jsonData);
});

calculateHorizontalTiles();
createMap(jsonData);
addClickListenerToMap();

let isMoving = false;

document.addEventListener('keydown', function(event) {
    const key = event.key;
    let direction;
    let steps = 1;  // Default to 1 step

    switch (key) {
        case 'ArrowUp':
            direction = 'up';
            break;
        case 'ArrowDown':
            direction = 'down';
            break;
        case 'ArrowLeft':
            direction = 'left';
            break;
        case 'ArrowRight':
            direction = 'right';
            break;
        case 'Escape':
            closePopup();
            return;
        default:
            return;
    }

    event.preventDefault();

    // Check if Shift key is pressed
    if (event.shiftKey) {
        steps = 10;  // Move 10 tiles when Shift is pressed
    }

    // Only process movement if not already moving
    if (!isMoving) {
        movePlayer(direction, steps);
    }
});

    function usePotion(potionName) {
        fetch('/use_potion', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `potion=${potionName}`
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            showMessage(data.message, data.success);
            console.log('Potion use result:', data);  // For debugging

            if (data.success) {
                updatePotionCount(potionName);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('An error occurred while using the potion.', false);
        });
    }

    function updatePotionCount(potionName) {
        const potionItem = document.querySelector(`.dropdown-item[data-potion="${potionName}"]`);
        if (potionItem) {
            const countSpan = potionItem.querySelector('.potion-count');
            if (countSpan) {
                let count = parseInt(countSpan.textContent);
                count--;
                if (count > 0) {
                    countSpan.textContent = count;
                } else {
                    // Remove the potion from the dropdown if count reaches 0
                    potionItem.parentElement.remove();
                }
            }
        }

        // Check if there are no more potions left
        const potionDropdown = document.getElementById('potionDropdown');
        if (potionDropdown.nextElementSibling.children.length === 0) {
            potionDropdown.innerHTML = 'No Potions';
            potionDropdown.classList.add('disabled');
        }
    }

    function showMessage(message, isSuccess) {
        const messageDisplay = document.getElementById('message-display');
        messageDisplay.textContent = message;
        messageDisplay.className = 'alert ' + (isSuccess ? 'alert-success' : 'alert-danger');
        messageDisplay.style.display = 'block';

        setTimeout(() => {
            messageDisplay.style.display = 'none';
        }, 3000);
    }

// Set up periodic refresh
const refreshInterval = 60000; // 60 seconds
setInterval(refreshMapData, refreshInterval);

// Initial refresh when the page loads
refreshMapData();