
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
                default:
                    return;
            }
            event.preventDefault();
            window.location.href = `/move?direction=${direction}`;
        });
