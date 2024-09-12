const gridSize = 80;
const verticalTiles = 20;

let horizontalTiles;

function calculateHorizontalTiles() {
    const mapContainer = document.querySelector('.map-container');
    horizontalTiles = Math.ceil(mapContainer.offsetWidth / gridSize) + 4;
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
            if (entity.control !== undefined) text += ` by ${entity.control}`;
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
    window.location.href = actionUrl;
}

function performDragAction(targetName, direction) {
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
    })
    .catch((error) => {
        console.error('Error:', error);
        displayMessage('An error occurred while dragging the player.');
    });
}

function dragPlayer(targetName, direction) {
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
    })
    .catch((error) => {
        console.error('Error:', error);
        displayMessage('An error occurred while dragging the player.');
    });
}

function closePopup() {
    const popup = document.getElementById('popup');
    popup.style.display = "none";
}

function moveToPosition(x, y, callback) {
    fetch(`/move_to?x=${x}&y=${y}&target=map`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        Object.assign(jsonData, data);
        updateMap(jsonData);

        if (data.message) {
            displayMessage(data.message);
        }

        const success = data.message && !data.message.includes("failed");
        callback(success);
        checkPlayerPosition();
    })
    .catch((error) => {
        console.error('Error:', error);
        displayMessage('An error occurred while moving.');
        callback(false);
    });
}

function performAction(actionUrl) {
    fetch(actionUrl)
        .then(response => response.json())
        .then(data => {
            Object.assign(jsonData, data);
            updateMap(jsonData);
            if (data.message) {
                displayMessage(data.message);
            }
            checkPlayerPosition();

            if (actionUrl.includes("rest")) {
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            displayMessage('An error occurred while performing the action.');
        });
}

function displayMessage(message) {
    const messageDisplay = document.getElementById('message-display');

    if (message && message.trim() !== '') {
        messageDisplay.textContent = message;
        messageDisplay.style.opacity = '1';
        messageDisplay.style.visibility = 'visible';

        setTimeout(() => {
            messageDisplay.style.opacity = '0';
            messageDisplay.style.visibility = 'hidden';
        }, 5000);

        setTimeout(() => {
            messageDisplay.textContent = '';
        }, 5300);
    } else {
        messageDisplay.textContent = '';
        messageDisplay.style.opacity = '0';
        messageDisplay.style.visibility = 'hidden';
    }
}

function addClickListenerToMap() {
    const mapContainer = document.getElementById("map");
    mapContainer.addEventListener("click", (event) => {
        if (event.target.classList.contains("tile") || event.target.closest(".entity")) {
            const clickedElement = event.target.classList.contains("tile") ? event.target : event.target.closest(".entity");
            const clickX = parseInt(clickedElement.style.left) / gridSize + 1;
            const clickY = parseInt(clickedElement.style.top) / gridSize + 1;

            moveToPosition(clickX, clickY, (success) => {
                if (success) {
                    updateMap(jsonData);
                }
            });
        }
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

window.addEventListener('resize', () => {
    calculateHorizontalTiles();
    updateMap(jsonData);
});

calculateHorizontalTiles();
createMap(jsonData);
addClickListenerToMap();

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

    // Function to move multiple steps
    function moveMultipleSteps(stepsRemaining) {
        if (stepsRemaining > 0) {
            fetch(`/move?direction=${direction}&target=map`)
                .then(response => response.json())
                .then(data => {
                    Object.assign(jsonData, data);
                    updateMap(jsonData);
                    if (data.message) {
                        displayMessage(data.message);
                    }
                    checkPlayerPosition();

                    // Continue moving if there are steps remaining and the move was successful
                    if (stepsRemaining > 1 && !data.message.includes("failed")) {
                        moveMultipleSteps(stepsRemaining - 1);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    displayMessage('An error occurred while moving.');
                });
        }
    }

    // Start the multi-step movement
    moveMultipleSteps(steps);
});


function buildPalisade() {
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
        // Assuming jsonData is a global variable holding the map data
        Object.assign(jsonData, data);
        updateMap(jsonData);
        checkPlayerPosition();
    })
    .catch((error) => {
        console.error('Error:', error);
        displayMessage('An error occurred while building the palisade.');
    });
}