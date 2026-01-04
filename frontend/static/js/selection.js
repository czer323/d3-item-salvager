(function () {
    'use strict';

    function handleEditClick(event) {
        const button = event.target.closest('[data-testid="selection-edit-button"]');
        if (!button) return;
        event.preventDefault();
        // Fetch the latest controls partial and replace the panel
        fetch('/frontend/selection/controls')
            .then((resp) => {
                if (!resp.ok) throw new Error('Failed to load selection controls');
                return resp.text();
            })
            .then((html) => {
                const panel = document.getElementById('selection-panel');
                if (!panel) return;
                // Replace content with the controls partial
                panel.innerHTML = html;
            })
            .catch((err) => {
                // TODO: show an inline error; for now, console
                console.error('selection: failed to load controls', err);
            });
    }

    document.addEventListener('click', handleEditClick);
})();
