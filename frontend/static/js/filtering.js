(function () {
    'use strict';

    const DEFAULT_DEBOUNCE_MS = 150;

    function normaliseToken(value) {
        return (value ?? '').toString().toLowerCase().replace(/[^a-z0-9]/g, '');
    }

    function fuzzyScore(candidate, query) {
        const candidateToken = normaliseToken(candidate);
        const queryToken = normaliseToken(query);
        if (!queryToken) {
            return 100;
        }
        if (!candidateToken) {
            return 0;
        }
        if (candidateToken.startsWith(queryToken)) {
            return 90 + Math.min(queryToken.length, 10);
        }
        const position = candidateToken.indexOf(queryToken);
        if (position !== -1) {
            return 75 + Math.max(0, 10 - position);
        }
        let matchIndex = 0;
        let gapPenalty = 0;
        for (const char of candidateToken) {
            if (matchIndex >= queryToken.length) {
                break;
            }
            if (char === queryToken[matchIndex]) {
                matchIndex += 1;
            } else if (matchIndex > 0) {
                gapPenalty += 1;
            }
        }
        if (matchIndex === queryToken.length) {
            return Math.max(30, 60 - gapPenalty);
        }
        return 0;
    }

    function debounce(fn, delay) {
        let timer = null;
        return function debounced(...args) {
            window.clearTimeout(timer);
            timer = window.setTimeout(() => fn.apply(this, args), delay);
        };
    }

    class ItemFilterController {
        constructor(root, state) {
            this.root = root;
            this.state = state;
            this.searchInput = null;
            this.slotSelect = null;
            this.clearButton = null;
            this.sectionNodes = [];
            this.debouncedApply = debounce(() => { this.applyFilters(); this.maybeTriggerServerRefresh(); }, DEFAULT_DEBOUNCE_MS);
            this.boundSearchHandler = null;
            this.boundSlotHandler = null;
            this.boundClearHandler = null;
            this.boundHtmxAfterRequest = null;
            this.pendingServerRequestTimerId = null;
            this.pendingServerRequest = false;
        }

        init() {
            if (!this.root) {
                return;
            }
            this.searchInput = this.root.querySelector('[data-filter-controls] [data-filter-search]');
            this.slotSelect = this.root.querySelector('[data-filter-controls] [data-filter-slot]');
            this.clearButton = this.root.querySelector('[data-filter-controls] [data-filter-clear]');
            this.sectionNodes = Array.from(this.root.querySelectorAll('[data-filter-section]'));

            // Record the server-provided search/slot so we can detect when the user
            // clears/changes the search and needs a server refresh.
            this.state.serverSearch = this.root.getAttribute('data-current-search') ?? '';
            this.state.serverSlot = this.root.getAttribute('data-current-slot') ?? '';
            this.pendingServerRequest = false;

            // Wire up an HTMX completion handler to clear the pending flag when the
            // server-side request finishes. Store the bound handler so it can be
            // removed later in destroy().
            if (window.htmx) {
                this.boundHtmxAfterRequest = (event) => {
                    try {
                        const target = event && event.detail && event.detail.target;
                        if (target && target.id === 'item-summary-content') {
                            this.pendingServerRequest = false;
                            if (this.pendingServerRequestTimerId) {
                                window.clearTimeout(this.pendingServerRequestTimerId);
                                this.pendingServerRequestTimerId = null;
                            }
                        }
                    } catch (e) {
                        // eslint-disable-next-line no-console
                        console.warn('htmx afterRequest handler failed', e);
                    }
                };
                window.htmx.on('htmx:afterRequest', this.boundHtmxAfterRequest);
            }

            if (this.searchInput) {
                if (this.state.search) {
                    this.searchInput.value = this.state.search;
                }
                this.boundSearchHandler = (event) => {
                    this.state.search = event.target.value ?? '';
                    this.debouncedApply();
                };
                this.searchInput.addEventListener('input', this.boundSearchHandler);
            }

            if (this.slotSelect) {
                if (this.state.slot) {
                    this.slotSelect.value = this.state.slot;
                }
                this.boundSlotHandler = (event) => {
                    this.state.slot = event.target.value ?? '';
                    this.applyFilters();
                };
                this.slotSelect.addEventListener('change', this.boundSlotHandler);
            }

            if (this.clearButton) {
                this.boundClearHandler = () => {
                    this.state.search = '';
                    this.state.slot = '';
                    if (this.searchInput) {
                        this.searchInput.value = '';
                        this.searchInput.focus();
                    }
                    if (this.slotSelect) {
                        this.slotSelect.value = '';
                    }
                    this.applyFilters();

                    // Reuse centralized server-refresh logic to avoid duplicating code.
                    // `triggerApply` already handles best-effort submit and warnings.
                    this.triggerApply();
                };
                this.clearButton.addEventListener('click', this.boundClearHandler);
            }

            this.applyFilters();
        }

        destroy() {
            if (this.searchInput && this.boundSearchHandler) {
                this.searchInput.removeEventListener('input', this.boundSearchHandler);
            }
            if (this.slotSelect && this.boundSlotHandler) {
                this.slotSelect.removeEventListener('change', this.boundSlotHandler);
            }
            if (this.clearButton && this.boundClearHandler) {
                this.clearButton.removeEventListener('click', this.boundClearHandler);
            }

            // Remove HTMX handler if registered and clear any fallback timer
            try {
                if (this.boundHtmxAfterRequest && window.htmx) {
                    window.htmx.off('htmx:afterRequest', this.boundHtmxAfterRequest);
                    this.boundHtmxAfterRequest = null;
                }
            } catch (e) {
                // eslint-disable-next-line no-console
                console.warn('Failed to remove htmx handler', e);
            }

            if (this.pendingServerRequestTimerId) {
                window.clearTimeout(this.pendingServerRequestTimerId);
                this.pendingServerRequestTimerId = null;
            }

            this.pendingServerRequest = false;
        }

        applyFilters() {
            const filtersActive = Boolean((this.state.search ?? '').trim() || (this.state.slot ?? '').trim());
            for (const section of this.sectionNodes) {
                this.applySectionFilters(section, filtersActive);
            }
        }

        // If the user clears the search (or changes it back to a value different
        // from the last server-provided search) we should refresh the server-rendered
        // summary so the DOM includes the correct set of items. This is a best-effort
        // check and uses a debounce to avoid excessive requests.
        maybeTriggerServerRefresh() {
            try {
                const current = (this.state.search ?? '').trim();
                const server = (this.state.serverSearch ?? '').trim();
                if (this.pendingServerRequest) {
                    return;
                }
                // trigger a refresh when the user clears the search while the server
                // had a non-empty search (i.e., they expect more items), or when the
                // server search differs from the current value and the current is empty
                // (covers manual clear) - keep condition minimal to avoid noisy requests.
                if (current === '' && server !== '') {
                    this.pendingServerRequest = true;
                    this.triggerApply();
                }
            } catch (e) {
                // swallow errors - not critical
                // eslint-disable-next-line no-console
                console.warn('maybeTriggerServerRefresh failed', e);
            }
        }

        triggerApply() {
            try {
                const applyBtn = document.querySelector('[data-testid="apply-filter-button"]');
                if (applyBtn) {
                    applyBtn.click();
                } else if (window.htmx) {
                    const selectionForm = document.querySelector('#selection-form');
                    if (selectionForm) {
                        htmx.trigger(selectionForm, 'submit');
                    }
                }
            } catch (e) {
                // eslint-disable-next-line no-console
                console.warn('triggerApply failed', e);
            }

            // Fallback: if HTMX isn't available, ensure we clear the pending flag
            // after a short timeout so the UI isn't permanently blocked.
            try {
                if (!window.htmx && this.pendingServerRequest) {
                    if (this.pendingServerRequestTimerId) {
                        window.clearTimeout(this.pendingServerRequestTimerId);
                    }
                    this.pendingServerRequestTimerId = window.setTimeout(() => {
                        this.pendingServerRequest = false;
                        this.pendingServerRequestTimerId = null;
                    }, 3000);
                }
            } catch (e) {
                // ignore
            }
        }

        applySectionFilters(section, filtersActive) {
            const items = Array.from(section.querySelectorAll('[data-filter-item]'));
            const list = section.querySelector('[data-filter-list]');
            const emptyState = section.querySelector('[data-filter-empty]');
            const countBadge = section.querySelector('[data-filter-count]');
            let visibleCount = 0;
            const slotValue = (this.state.slot ?? '').toLowerCase();
            const searchValue = (this.state.search ?? '').trim();

            for (const item of items) {
                const itemSlot = (item.getAttribute('data-item-slot') ?? '').toLowerCase();
                const itemName = item.getAttribute('data-item-name') ?? '';
                const slotMatches = !slotValue || itemSlot === slotValue;
                let matches = slotMatches;
                if (matches && searchValue) {
                    matches = fuzzyScore(itemName, searchValue) > 0;
                }
                if (matches) {
                    visibleCount += 1;
                    item.hidden = false;
                    item.setAttribute('aria-hidden', 'false');
                } else {
                    item.hidden = true;
                    item.setAttribute('aria-hidden', 'true');
                }
            }

            if (countBadge) {
                countBadge.textContent = String(visibleCount);
            }
            if (emptyState) {
                const defaultMessage = emptyState.getAttribute('data-empty-default') ?? emptyState.textContent ?? '';
                const filteredMessage = emptyState.getAttribute('data-empty-filtered') ?? defaultMessage;
                emptyState.textContent = filtersActive ? filteredMessage : defaultMessage;
            }

            if (visibleCount > 0) {
                if (list) {
                    list.hidden = false;
                }
                if (emptyState) {
                    emptyState.hidden = true;
                }
            } else {
                if (list) {
                    list.hidden = true;
                }
                if (emptyState) {
                    emptyState.hidden = false;
                }
            }

            section.dataset.filteredCount = String(visibleCount);
            section.dataset.filtersActive = filtersActive ? 'true' : 'false';
        }
    }

    const Filtering = {
        controller: null,
        state: {
            search: '',
            slot: '',
        },
        init(root) {
            if (!root) {
                return;
            }
            if (this.controller) {
                this.controller.destroy();
            }
            const existingSearch = root.getAttribute('data-current-search') ?? '';
            const existingSlot = root.getAttribute('data-current-slot') ?? '';
            this.state.search = existingSearch;
            this.state.slot = existingSlot;
            this.controller = new ItemFilterController(root, this.state);
            this.controller.init();
            window.d3Filtering = {
                state: this.state,
            };
        },
    };

    document.addEventListener('DOMContentLoaded', () => {
        const root = document.querySelector('[data-filter-root]');
        Filtering.init(root);
    });

    if (window.htmx) {
        window.htmx.on('htmx:afterSwap', (event) => {
            const target = event.detail && event.detail.target;
            if (target && target.id === 'item-summary-content') {
                Filtering.init(target.querySelector('[data-filter-root]'));
            }
        });

        window.htmx.on('htmx:configRequest', (event) => {
            const detail = event.detail;
            if (!detail) {
                return;
            }
            const path = detail.path ?? '';
            if (!path.includes('/frontend/items') || path.endsWith('.json')) {
                return;
            }
            detail.parameters = detail.parameters || {};
            const state = Filtering.state;
            if (state.search) {
                detail.parameters.search = state.search;
            }
            if (state.slot) {
                detail.parameters.slot = state.slot;
            }
        });
    }
})();
