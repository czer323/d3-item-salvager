(function () {
    'use strict';

    const STORAGE_KEY = 'd3-item-salvager.preferences';
    const DEFAULT_PAYLOAD = Object.freeze({
        version: 2,
        classes: [],
        builds: [],
    });
    const DEFAULTS_SCRIPT_ID = 'preferences-defaults';
    const OPEN_BUTTON_TEST_ID = 'preferences-open-button';
    const MODAL_ID = 'preferences-modal';
    const TOAST_ID = 'preferences-toast';
    const SAVE_BUTTON_TEST_ID = 'preferences-save-button';
    const EXPORT_BUTTON_TEST_ID = 'preferences-export-button';
    const IMPORT_BUTTON_TEST_ID = 'preferences-import-button';
    const EDITOR_TEST_ID = 'preferences-json-editor';
    const CONTROLS_CARD_ID = 'selection-controls';
    const FORM_ID = 'selection-form';

    function readDefaults() {
        const script = document.getElementById(DEFAULTS_SCRIPT_ID);
        if (!script) {
            return DEFAULT_PAYLOAD;
        }
        try {
            const raw = script.textContent ?? '';
            if (!raw.trim()) {
                return DEFAULT_PAYLOAD;
            }
            const parsed = JSON.parse(raw);
            const version = typeof parsed.version === 'number' ? parsed.version : DEFAULT_PAYLOAD.version;
            const classes = normaliseList(parsed.classes);
            const builds = normaliseList(parsed.builds);
            return {
                version,
                classes,
                builds,
            };
        } catch (_error) {
            return DEFAULT_PAYLOAD;
        }
    }

    function normaliseList(value) {
        if (!value) {
            return [];
        }
        const iterable = Array.isArray(value) ? value : [];
        const seen = new Set();
        const result = [];
        for (const entry of iterable) {
            const text = String(entry ?? '').trim();
            if (!text || seen.has(text)) {
                continue;
            }
            seen.add(text);
            result.push(text);
        }
        return result;
    }

    class Toast {
        constructor(root) {
            this.root = root;
            this.clearTimer = null;
        }

        show(message, intent = 'success') {
            if (!this.root) {
                return;
            }
            window.clearTimeout(this.clearTimer);
            const alert = document.createElement('div');
            alert.className = intentToAlertClass(intent);
            alert.textContent = message;
            this.root.innerHTML = '';
            this.root.appendChild(alert);
            this.root.classList.remove('hidden');
            this.clearTimer = window.setTimeout(() => {
                this.root.classList.add('hidden');
            }, 3200);
        }
    }

    function intentToAlertClass(intent) {
        switch (intent) {
            case 'info':
                return 'alert alert-info shadow';
            case 'warning':
                return 'alert alert-warning shadow';
            case 'error':
                return 'alert alert-error shadow';
            case 'success':
            default:
                return 'alert alert-success shadow';
        }
    }

    class PreferencesManager {
        constructor(defaultPayload) {
            this.defaults = {
                version: defaultPayload.version ?? DEFAULT_PAYLOAD.version,
                classes: normaliseList(defaultPayload.classes),
                builds: normaliseList(defaultPayload.builds),
            };
            this.storageKey = STORAGE_KEY;
            this.pendingState = null;
            this.toast = new Toast(document.getElementById(TOAST_ID));
        }

        init() {
            window.d3Preferences = {
                storageKey: this.storageKey,
                version: this.defaults.version,
            };
            this.bindModalHandlers();
            this.bindControlHandlers();
            this.bindHtmxHooks();
            const initialState = this.restoreFromStorage();
            this.applyState(initialState, { initial: true });
        }

        bindModalHandlers() {
            const modal = document.getElementById(MODAL_ID);
            if (!modal) {
                return;
            }

            const saveButton = document.querySelector(`[data-testid="${SAVE_BUTTON_TEST_ID}"]`);
            if (saveButton && !saveButton.dataset.preferencesBound) {
                saveButton.dataset.preferencesBound = 'true';
                saveButton.addEventListener('click', (event) => {
                    event.preventDefault();
                    const state = this.captureCurrentState();
                    this.writeToStorage(state);
                    this.toast.show('Preferences saved');
                });
            }

            const exportButton = document.querySelector(`[data-testid="${EXPORT_BUTTON_TEST_ID}"]`);
            if (exportButton && !exportButton.dataset.preferencesBound) {
                exportButton.dataset.preferencesBound = 'true';
                exportButton.addEventListener('click', (event) => {
                    event.preventDefault();
                    const state = this.captureCurrentState();
                    const editor = this.getEditor();
                    if (!editor) {
                        return;
                    }
                    editor.value = JSON.stringify(state, null, 2);
                    editor.focus();
                    editor.select();
                    this.toast.show('Preferences exported to JSON', 'info');
                });
            }

            const importButton = document.querySelector(`[data-testid="${IMPORT_BUTTON_TEST_ID}"]`);
            if (importButton && !importButton.dataset.preferencesBound) {
                importButton.dataset.preferencesBound = 'true';
                importButton.addEventListener('click', (event) => {
                    event.preventDefault();
                    this.handleImport();
                });
            }
        }

        bindControlHandlers() {
            const modal = document.getElementById(MODAL_ID);
            if (!modal) {
                return;
            }
            const openButton = document.querySelector(`[data-testid="${OPEN_BUTTON_TEST_ID}"]`);
            if (openButton && !openButton.dataset.preferencesBound) {
                openButton.dataset.preferencesBound = 'true';
                openButton.addEventListener('click', () => {
                    modal.showModal();
                });
            }
        }

        bindHtmxHooks() {
            if (!window.htmx) {
                return;
            }
            window.htmx.on('htmx:afterSwap', (event) => {
                const target = event.detail && event.detail.target;
                if (target && target.id === CONTROLS_CARD_ID) {
                    this.bindControlHandlers();
                    if (this.pendingState) {
                        this.applyState(this.pendingState, { skipTrigger: true });
                    }
                }
            });
        }

        restoreFromStorage() {
            try {
                const raw = window.localStorage.getItem(this.storageKey);
                if (!raw) {
                    return this.defaults;
                }
                const parsed = JSON.parse(raw);
                const parsedVersion = typeof parsed.version === 'number' ? parsed.version : DEFAULT_PAYLOAD.version;
                if (parsedVersion > this.defaults.version) {
                    this.toast.show('Saved preferences are from a newer version and cannot be loaded.', 'warning');
                    return this.defaults;
                }
                return {
                    version: this.defaults.version,
                    classes: normaliseList(parsed.classes) || this.defaults.classes,
                    builds: normaliseList(parsed.builds) || this.defaults.builds,
                };
            } catch (_error) {
                this.toast.show('Failed to read saved preferences from localStorage.', 'error');
                return this.defaults;
            }
        }

        writeToStorage(state) {
            try {
                window.localStorage.setItem(this.storageKey, JSON.stringify(state));
            } catch (_error) {
                this.toast.show('Unable to persist preferences to localStorage.', 'error');
            }
        }

        handleImport() {
            const editor = this.getEditor();
            if (!editor) {
                return;
            }
            const raw = editor.value.trim();
            if (!raw) {
                this.toast.show('Paste a preferences JSON payload before importing.', 'warning');
                return;
            }
            try {
                const parsed = JSON.parse(raw);
                const parsedVersion = typeof parsed.version === 'number' ? parsed.version : DEFAULT_PAYLOAD.version;
                if (parsedVersion > this.defaults.version) {
                    this.toast.show('Imported preferences are incompatible with this version.', 'error');
                    return;
                }
                const state = {
                    version: this.defaults.version,
                    classes: normaliseList(parsed.classes),
                    builds: normaliseList(parsed.builds),
                };
                this.writeToStorage(state);
                this.applyState(state, { initial: true });
                this.toast.show('Preferences imported. Selections updated.', 'success');
            } catch (_error) {
                this.toast.show('Invalid JSON payload supplied for import.', 'error');
            }
        }

        captureCurrentState() {
            const form = document.getElementById(FORM_ID);
            const classes = this.collectSelectValues(form, 'class_ids');
            const builds = this.collectSelectValues(form, 'build_ids');
            return {
                version: this.defaults.version,
                classes,
                builds,
            };
        }

        applyState(state, options = {}) {
            const form = document.getElementById(FORM_ID);
            if (!form) {
                this.pendingState = state;
                return;
            }

            const classSelect = form.querySelector('select[name="class_ids"]');
            const buildSelect = form.querySelector('select[name="build_ids"]');
            this.applySelectValues(classSelect, state.classes);
            this.applySelectValues(buildSelect, state.builds);
            this.pendingState = null;
        }

        getEditor() {
            return document.querySelector(`[data-testid="${EDITOR_TEST_ID}"]`);
        }

        collectSelectValues(root, name) {
            if (!root) {
                return [];
            }
            const select = root.querySelector(`select[name="${name}"]`);
            if (!select) {
                return [];
            }
            const values = [];
            Array.from(select.options).forEach((option) => {
                if (option.selected) {
                    const value = String(option.value ?? '').trim();
                    if (value && !values.includes(value)) {
                        values.push(value);
                    }
                }
            });
            return values;
        }

        applySelectValues(select, values) {
            if (!select) {
                return;
            }
            const target = new Set(values ?? []);
            Array.from(select.options).forEach((option) => {
                if (target.size === 0) {
                    option.selected = false;
                } else {
                    option.selected = target.has(option.value);
                }
            });
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        const defaults = readDefaults();
        const manager = new PreferencesManager(defaults);
        manager.init();
    });
})();
