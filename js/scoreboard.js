function adjustGrid() {
            const grids = document.querySelectorAll('.card-grid');
            grids.forEach(grid => {
                const containerWidth = grid.offsetWidth;
                const cardWidth = 200; // Minimum card width
                const columns = Math.floor(containerWidth / cardWidth);
                grid.style.gridTemplateColumns = `repeat(${columns}, 1fr)`;
            });
        }

        window.addEventListener('load', adjustGrid);
        window.addEventListener('resize', adjustGrid);

        // Search functionality for players
        const playerSearch = document.getElementById('playerSearch');
        const playerGrid = document.getElementById('playerGrid');

        playerSearch.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const players = playerGrid.getElementsByClassName('card');

            Array.from(players).forEach(function(player) {
                const playerInfo = player.textContent.toLowerCase();
                if (playerInfo.includes(searchTerm)) {
                    player.style.display = 'block';
                } else {
                    player.style.display = 'none';
                }
            });
        });

        // Search functionality for map items
        const mapSearch = document.getElementById('mapSearch');
        const mapGrid = document.getElementById('mapGrid');

        mapSearch.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const mapItems = mapGrid.getElementsByClassName('card');

            Array.from(mapItems).forEach(function(item) {
                const itemInfo = item.textContent.toLowerCase();
                if (itemInfo.includes(searchTerm)) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
        });