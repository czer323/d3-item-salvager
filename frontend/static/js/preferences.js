(function () {
    'use strict';

    const STORAGE_KEY = 'd3-item-salvager.preferences';
    const DEFAULT_PAYLOAD = Object.freeze({
        version: 1,
        classes: [],
        builds: [],
        variants: [],
    });
    const DEFAULTS_SCRIPT_ID = 'preferences-defaults';
    const OPEN_BUTTON_TEST_ID = 'preferences-open-button';
    const MODAL_ID = 'preferences-modal';
    const TOAST_ID = 'preferences-toast';
    const SAVE_BUTTON_TEST_ID = 'preferences-save-button';
    const EXPORT_BUTTON_TEST_ID = 'preferences-export-button';
    const IMPORT_BUTTON_TEST_ID = 'preferences-import-button';
    const EDITOR_TEST_ID = 'preferences-json-editor';
    const CONTROLS_ID = 'selection-controls';

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
            const variants = normaliseList(parsed.variants);
            return {
                version,
                classes,
                builds,
                variants,
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
                variants: normaliseList(defaultPayload.variants),
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
                if (target && target.id === CONTROLS_ID) {
                    this.bindControlHandlers();
                    if (this.pendingState) {
                        this.applyState(this.pendingState, { initial: false });
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
                if (typeof parsed.version !== 'number' || parsed.version !== this.defaults.version) {
                    this.toast.show('Saved preferences are outdated. Please re-save.', 'warning');
                    return this.defaults;
                }
                return {
                    version: this.defaults.version,
                    classes: normaliseList(parsed.classes),
                    builds: normaliseList(parsed.builds),
                    variants: normaliseList(parsed.variants) || this.defaults.variants,
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
                if (typeof parsed.version !== 'number' || parsed.version !== this.defaults.version) {
                    this.toast.show('Imported preferences are incompatible with this version.', 'error');
                    return;
                }
                const state = {
                    version: this.defaults.version,
                    classes: normaliseList(parsed.classes),
                    builds: normaliseList(parsed.builds),
                    variants: normaliseList(parsed.variants) || this.defaults.variants,
                };
                this.writeToStorage(state);
                this.applyState(state, { initial: true });
                this.toast.show('Preferences imported. Selections updated.', 'success');
            } catch (_error) {
                this.toast.show('Invalid JSON payload supplied for import.', 'error');
            }
        }

        captureCurrentState() {
            const controls = document.getElementById(CONTROLS_ID);
            const classes = [];
            const builds = [];
            const variants = [];
            if (controls) {
                const classSelect = controls.querySelector('[data-testid="class-select"]');
                const buildSelect = controls.querySelector('[data-testid="build-select"]');
                const variantSelect = controls.querySelector('[data-testid="variant-select"]');
                this.maybeAppendValue(classSelect, classes);
                this.maybeAppendValue(buildSelect, builds);
                this.maybeAppendValue(variantSelect, variants);
            }
            return {
                version: this.defaults.version,
                classes,
                builds,
                variants: variants.length ? variants : this.defaults.variants,
            };
        }

        maybeAppendValue(select, target) {
            if (!select) {
                return;
            }
            const value = String(select.value ?? '').trim();
            if (value && !target.includes(value)) {
                target.push(value);
            }
        }

        applyState(state, options = {}) {
            const controls = document.getElementById(CONTROLS_ID);
            if (!controls) {
                this.pendingState = state;
                return;
            }

            const classSelect = controls.querySelector('[data-testid="class-select"]');
            const buildSelect = controls.querySelector('[data-testid="build-select"]');
            const variantSelect = controls.querySelector('[data-testid="variant-select"]');

            const classTarget = state.classes[0] ?? null;
            const buildTarget = state.builds[0] ?? null;
            const variantTarget = state.variants[0] ?? null;

            const changeEventOptions = { bubbles: true };
            const isInitialApply = Boolean(options && options.initial);
            let triggeredRefresh = false;
            if (classSelect && classTarget && classSelect.value !== classTarget) {
                if (this.setSelectValue(classSelect, classTarget, false)) {
                    if (isInitialApply) {
                        triggeredRefresh = true;
                        classSelect.dispatchEvent(new Event('change', changeEventOptions));
                    }
                } else {
                    this.toast.show('Saved class is no longer available.', 'warning');
                }
            }

            if (triggeredRefresh) {
                this.pendingState = state;
                return;
            }

            if (buildSelect && buildTarget && buildSelect.value !== buildTarget) {
                if (!this.setSelectValue(buildSelect, buildTarget, false)) {
                    this.toast.show('Saved build is no longer available.', 'warning');
                }
            }
            if (variantSelect && variantTarget) {
                if (!this.setSelectValue(variantSelect, variantTarget, true)) {
                    this.toast.show('Saved variant is no longer available.', 'warning');
                }
            }

            this.pendingState = null;
        }

        setSelectValue(select, value, triggerChange) {
            if (!select || !value) {
                return false;
            }
            const option = Array.from(select.options).find((item) => item.value === value);
            if (!option) {
                return false;
            }
            const needsChange = select.value !== value;
            if (needsChange) {
                select.value = value;
            }
            if (triggerChange) {
                select.dispatchEvent(new Event('change', { bubbles: true }));
            }
            return true;
        }

        getEditor() {
            return document.querySelector(`[data-testid="${EDITOR_TEST_ID}"]`);
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        const defaults = readDefaults();
        const manager = new PreferencesManager(defaults);
        manager.init();
    });
})();
