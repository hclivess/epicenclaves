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
            if (entity.level !== undefined) text += ` Lvl${entity.level}`;
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

        fragment.appendChild(element);
        return element;
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

function updatePopupContent(x_pos, y_pos, tileType) {
    const popup = document.getElementById('popup');
    const currentTile = `${x_pos},${y_pos}`;
    const tileActions = jsonData.actions[currentTile] || [];

    let popupContent = `
        <h3>Tile Information</h3>
        <p>You arrive at <strong>${tileType}</strong></p>
    `;

    if (tileActions.length > 0) {
        tileActions.forEach(action => {
           if (action.action.startsWith('/fight')) {
                popupContent += `<button onclick="performFightAction('${action.action}')">${action.name}</button>`;
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

function performFightAction(actionUrl) {
    // Navigate to the fight page
    window.location.href = actionUrl;
}

function closePopup() {
    const popup = document.getElementById('popup');
    popup.style.display = "none";
}

function checkPlayerPosition() {
    const currentUserData = jsonData.users[currentUser];
    if (currentUserData) {
        const { x_pos, y_pos } = currentUserData;
        const key = `${x_pos},${y_pos}`;
        const entityOnTile = jsonData.construction[key];

        const playerElement = document.querySelector('.entity.player');
        const exclamationMark = playerElement.querySelector('.exclamation-mark');

        if (entityOnTile) {
            exclamationMark.style.display = "flex";
            updatePopupContent(x_pos, y_pos, entityOnTile.type);
        } else {
            exclamationMark.style.display = "none";
            closePopup();
        }
    }
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
                // Reload the page after a short delay
                setTimeout(() => {
                    window.location.reload();
                }, 0);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            displayMessage('An error occurred while performing the action.');
        });
}

function displayMessage(message) {
    const messageDisplay = document.getElementById('message-display');
    if (messageDisplay) {
        messageDisplay.textContent = message;
        messageDisplay.style.display = 'block';
        setTimeout(() => {
            messageDisplay.style.display = 'none';
        }, 5000); // Hide the message after 5 seconds
    } else {
        console.log("Message:", message);
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
    fetch(`/move?direction=${direction}&target=map`)
        .then(response => response.json())
        .then(data => {
            Object.assign(jsonData, data);
            updateMap(jsonData);
            if (data.message) {
                displayMessage(data.message);
            }
            checkPlayerPosition();
        })
        .catch(error => {
            console.error('Error:', error);
            displayMessage('An error occurred while moving.');
        });
});