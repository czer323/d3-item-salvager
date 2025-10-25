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
            this.debouncedApply = debounce(() => this.applyFilters(), DEFAULT_DEBOUNCE_MS);
            this.boundSearchHandler = null;
            this.boundSlotHandler = null;
            this.boundClearHandler = null;
        }

        init() {
            if (!this.root) {
                return;
            }
            this.searchInput = this.root.querySelector('[data-filter-controls] [data-filter-search]');
            this.slotSelect = this.root.querySelector('[data-filter-controls] [data-filter-slot]');
            this.clearButton = this.root.querySelector('[data-filter-controls] [data-filter-clear]');
            this.sectionNodes = Array.from(this.root.querySelectorAll('[data-filter-section]'));

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
        }

        applyFilters() {
            const filtersActive = Boolean((this.state.search ?? '').trim() || (this.state.slot ?? '').trim());
            for (const section of this.sectionNodes) {
                this.applySectionFilters(section, filtersActive);
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
