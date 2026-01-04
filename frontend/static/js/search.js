(function () {
    "use strict";

    const STATUS_CLASSES = {
        base: "mt-2 text-sm text-base-content/60",
        success: "mt-2 text-sm text-success",
        error: "mt-2 text-sm text-error",
    };

    function clearStatus(el) {
        el.hidden = true;
        el.textContent = "";
        el.className = STATUS_CLASSES.base;
    }

    function setStatus(el, text, severity) {
        if (!text) {
            clearStatus(el);
            return;
        }
        const className =
            severity === "success"
                ? STATUS_CLASSES.success
                : severity === "error"
                    ? STATUS_CLASSES.error
                    : STATUS_CLASSES.base;
        el.hidden = false;
        el.textContent = text;
        el.className = className;
    }

    function getRowByItemId(itemId) {
        if (!itemId) {
            return null;
        }
        return document.querySelector(`[data-filter-item][data-item-id="${itemId}"]`);
    }

    function hasMatchingRow(query) {
        if (!query) {
            return false;
        }
        const normalized = query.toLowerCase();
        const rows = document.querySelectorAll("[data-filter-item]");
        return Array.from(rows).some((row) => {
            const name = row.getAttribute("data-item-name");
            return name && name.toLowerCase().includes(normalized);
        });
    }

    function initSearch(root) {
        const input = root.querySelector("[data-filter-search]");
        const statusEl = root.querySelector("[data-testid=\"search-status\"]");
        const lookupUrl = root.getAttribute("data-lookup-url") || "/items/lookup";

        if (!input || !statusEl) {
            return;
        }

        let timer = null;
        input.addEventListener("input", () => {
            const query = input.value.trim();
            if (timer) {
                clearTimeout(timer);
            }
            if (!query) {
                clearStatus(statusEl);
                return;
            }

            timer = setTimeout(() => {
                fetch(`${lookupUrl}?query=${encodeURIComponent(query)}`)
                    .then((r) => r.json())
                    .then((payload) => {
                        clearStatus(statusEl);
                        if (payload.match_type === "exact" && payload.item) {
                            if (!getRowByItemId(payload.item.id)) {
                                setStatus(
                                    statusEl,
                                    "Exact match found in the catalog; that item is not part of your build and can be salvaged.",
                                    "success"
                                );
                            }
                            return;
                        }

                        if (hasMatchingRow(query)) {
                            return;
                        }

                        if (payload.match_type === "fuzzy" && Array.isArray(payload.suggestions)) {
                            const names = payload.suggestions
                                .map((item) => item?.name)
                                .filter(Boolean);
                            if (names.length === 1) {
                                setStatus(
                                    statusEl,
                                    `Partial match: ${names[0]}. That item is safe to delete if it is not part of your builds.`,
                                    "success"
                                );
                                return;
                            }
                            if (names.length > 1) {
                                setStatus(
                                    statusEl,
                                    `Possible matches: ${names.join(", ")}. Check spelling or ensure they belong to this build.`,
                                    "error"
                                );
                                return;
                            }
                        }

                        if (payload.match_type === "fuzzy") {
                            setStatus(statusEl, "Item not found. Check spelling or try a different name.", "error");
                        } else if (payload.match_type === "none") {
                            setStatus(statusEl, "Item not found in the catalog. Check spelling.", "error");
                        }
                    })
                    .catch(() => {
                        setStatus(statusEl, "Search failed. Try again later.", "error");
                    });
            }, 200);
        });
    }

    function init() {
        const root = document.querySelector("[data-filter-controls]");
        if (root) {
            initSearch(root);
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

    if (window.htmx && typeof window.htmx.on === "function") {
        window.htmx.on("htmx:afterSwap", (event) => {
            const target = event.detail && event.detail.target;
            if (target && target.querySelector && target.querySelector("[data-filter-controls]")) {
                init();
            }
        });
    }
})();
