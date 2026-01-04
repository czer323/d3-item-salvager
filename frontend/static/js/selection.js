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

    function handleEnterKey(event) {
        if (event.key !== 'Enter') return;
        const active = document.activeElement;
        if (!active) return;
        // If focus is inside the selection panel, submit the form with action=apply_items
        const panel = active.closest && active.closest('#selection-panel');
        if (!panel) return;
        const form = panel.querySelector('#selection-form');
        if (!form) return;

        // Prevent default and programmatically submit with action=apply_items
        event.preventDefault();

        // Ensure an action input exists and set its value to 'apply_items'
        let actionInput = form.querySelector('input[name="action"][type="hidden"]');
        if (!actionInput) {
            actionInput = document.createElement('input');
            actionInput.type = 'hidden';
            actionInput.name = 'action';
            form.appendChild(actionInput);
        }
        actionInput.value = 'apply_items';

        // Submit the form (HTMX will honor hx-post attributes)
        form.querySelector('[type="submit"]')?.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    }

    document.addEventListener('click', handleEditClick);
    document.addEventListener('keydown', handleEnterKey);
})();
