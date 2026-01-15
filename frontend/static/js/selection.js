(function () {
    'use strict';

    function handleEditClick(event) {
        const button = event.target.closest('[data-testid="selection-edit-button"]');
        if (!button) return;
        event.preventDefault();

        // Prevent concurrent fetches by aborting the previous one (if any) or
        // disabling the button while a fetch is in flight.
        if (button._selectionFetchController) {
            try {
                button._selectionFetchController.abort();
            } catch (e) {
                // ignore
            }
        }

        const controller = typeof window.AbortController === 'function' ? new AbortController() : null;
        button._selectionFetchController = controller;
        button.disabled = true;
        button.setAttribute('aria-busy', 'true');

        const fetchOptions = controller ? { signal: controller.signal } : {};

        fetch('/frontend/selection/controls', fetchOptions)
            .then((resp) => {
                if (!resp.ok) throw new Error('Failed to load selection controls');
                return resp.text();
            })
            .then((html) => {
                const panel = document.getElementById('selection-panel');
                if (!panel) return;

                // Parse the returned HTML into a template, then perform light sanitisation
                // to protect against accidental script injection in the fragment.
                const template = document.createElement('template');
                template.innerHTML = html;

                // Remove script elements
                const scripts = template.content.querySelectorAll('script');
                if (scripts.length) {
                    console.warn('selection: removed <script> tags from fetched controls');
                    scripts.forEach((s) => s.remove());
                }

                // Remove inline event handler attributes (on*) and javascript: src attributes
                const elems = template.content.querySelectorAll('*');
                for (const el of elems) {
                    for (const { name, value } of Array.from(el.attributes)) {
                        if (name.startsWith('on')) {
                            el.removeAttribute(name);
                        }
                        if ((name === 'src' || name === 'href') && typeof value === 'string' && value.trim().toLowerCase().startsWith('javascript:')) {
                            el.removeAttribute(name);
                        }
                    }
                }

                // Replace panel contents with the (sanitised) fragment
                panel.replaceChildren(template.content.cloneNode(true));
            })
            .catch((err) => {
                if (err && err.name === 'AbortError') {
                    // Previous request was aborted — this is expected in some flows.
                    console.info('selection: previous controls fetch aborted');
                    return;
                }
                console.error('selection: failed to load controls', err);
            })
            .finally(() => {
                // Re-enable button and clear controller so UI recovers.
                try { button.disabled = false; } catch (e) {}
                button.removeAttribute('aria-busy');
                button._selectionFetchController = null;
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

        // Prefer programmatic submit with a temporary submitter to avoid leaving a persistent hidden input
        if (typeof form.requestSubmit === 'function') {
            const tempBtn = document.createElement('button');
            tempBtn.type = 'submit';
            tempBtn.name = 'action';
            tempBtn.value = 'apply_items';
            tempBtn.style.display = 'none';
            form.appendChild(tempBtn);
            // Use requestSubmit to pass the temporary submitter value
            try {
                form.requestSubmit(tempBtn);
            } finally {
                // Remove temporary button after a short delay to allow submission lifecycle
                setTimeout(() => tempBtn.remove(), 50);
            }
        } else {
            // Fallback for older browsers: add transient hidden input and attempt a real button click.
            // Calling .click() on a submit button usually triggers validation and submit handlers.
            // If no submit button exists, fall back to form.submit() (note: this bypasses validation and submit handlers).
            let actionInput = form.querySelector('input[name="action"][type="hidden"]');
            if (!actionInput) {
                actionInput = document.createElement('input');
                actionInput.type = 'hidden';
                actionInput.name = 'action';
                form.appendChild(actionInput);
            }
            actionInput.value = 'apply_items';

            const submitBtn = form.querySelector('[type="submit"]');
            if (submitBtn && typeof submitBtn.click === 'function') {
                // Clean up the transient input after the form actually submits.
                const cleanup = () => {
                    try { actionInput.remove(); } catch (e) {}
                    form.removeEventListener('submit', cleanup);
                };
                form.addEventListener('submit', cleanup, { once: true });
                // Programmatic click should trigger the normal submit flow (including validation)
                submitBtn.click();
            } else {
                // As a last resort, use form.submit(). This bypasses validation and submit handlers.
                try {
                    form.submit();
                } finally {
                    try { actionInput.remove(); } catch (e) {}
                }
            }
        }
    }

    document.addEventListener('click', handleEditClick);
    document.addEventListener('keydown', handleEnterKey);

    // Listen for search actions and provide light integration points
    window.addEventListener('search:add', (ev) => {
        // Currently, selection actions are persisted to localStorage by the search component.
        // This listener is a hook for enhancing the selection UI (e.g., visual feedback).
        console.info('selection: item added from search', ev.detail);
    });

    window.addEventListener('search:salvage', (ev) => {
        console.info('selection: item marked salvage from search', ev.detail);
    });
})();
