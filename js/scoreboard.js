document.addEventListener('DOMContentLoaded', function() {
    // Player filtering
    const playerSearch = document.getElementById('playerSearch');
    const playerGrid = document.getElementById('playerGrid');
    const players = Array.from(playerGrid.getElementsByClassName('card'));

    function filterPlayers() {
        const searchTerm = playerSearch.value.toLowerCase();
        players.forEach(player => {
            const playerInfo = player.textContent.toLowerCase();
            player.style.display = playerInfo.includes(searchTerm) ? '' : 'none';
        });
    }

    playerSearch.addEventListener('input', filterPlayers);

    // Map filtering
    const mapSearch = document.getElementById('mapSearch');
    const mapGrid = document.getElementById('mapGrid');
    const mapItems = Array.from(mapGrid.getElementsByClassName('card'));

    function filterMap() {
        const searchTerm = mapSearch.value.toLowerCase();
        mapItems.forEach(item => {
            const itemInfo = item.textContent.toLowerCase();
            item.style.display = itemInfo.includes(searchTerm) ? '' : 'none';
        });
    }

    mapSearch.addEventListener('input', filterMap);
});