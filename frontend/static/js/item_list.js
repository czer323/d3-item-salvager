// Client-side wiring to fetch /builds/items and render into #item-list (T011)

async function fetchBuildItems(buildIds = [], { limit = 100, offset = 0 } = {}) {
    // Validate buildIds up-front: if none are selected, return an empty payload
    if (!buildIds || !Array.isArray(buildIds) || buildIds.length === 0) {
        return { data: [] };
    }

    const params = new URLSearchParams();
    // Backend expects a comma-separated list (e.g., "1,2,3"); only set when present
    params.set('build_ids', buildIds.join(','));
    params.set('limit', String(limit));
    params.set('offset', String(offset));

    // Prefer an explicit meta config, then template data attribute, then legacy DOM content
    let backendBase = document.querySelector('meta[name="backend-base"]')?.content || '';

    if (!backendBase) {
        const filterRoot = document.querySelector('[data-filter-controls]');
        if (filterRoot) {
            const lookup = filterRoot.getAttribute('data-lookup-url') || '';
            // lookup is like "http://.../items/lookup" - strip the suffix to get base
            backendBase = lookup.replace(/\/items\/lookup$/, '');
        }
    }

    if (!backendBase) {
        const mono = document.querySelector('span.font-mono');
        if (mono) {
            const m = mono.textContent && mono.textContent.match(/https?:\/\/[^\s]+/);
            if (m) backendBase = m[0];
        }
    }

    if (!backendBase) backendBase = 'http://127.0.0.1:8000';

    const url = `${backendBase}/builds/items?${params.toString()}`;

    const res = await fetch(url, {
        headers: { 'Accept': 'application/json' },
    });
    if (!res.ok) {
        const text = await res.text().catch(() => '');
        console.error('Item list fetch failed', res.status, text);
        throw new Error(`Failed to fetch build items (${res.status})`);
    }
    return res.json();
}

function dedupeAndSort(items = []) {
    const seen = new Set();
    const unique = [];
    for (const it of items) {
        // Prefer a stable `id` when available, then a case-normalised name, then
        // fall back to a stable index-based key to avoid collapsing multiple
        // items that lack both `id` and `name`.
        const key = it.id != null
            ? `id:${String(it.id)}`
            : (it.name ? `name:${String(it.name).toLowerCase()}` : `idx:${unique.length}`);
        if (seen.has(key)) continue;
        seen.add(key);
        unique.push(it);
    }
    unique.sort((a, b) => (a.name || '').localeCompare(b.name || ''));
    return unique;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    // Ensure null/undefined are treated as empty strings
    div.textContent = text ?? '';
    return div.innerHTML;
}

function renderItems(items) {
    let container = document.querySelector('#item-list');

    // If target container isn't present (e.g., no selection applied), create it
    if (!container) {
        const target = document.querySelector('#item-summary-content');
        if (target) {
            container = document.createElement('div');
            container.id = 'item-list';
            container.setAttribute('data-virtual-list', '');
            target.prepend(container);
        } else {
            // As a last resort, append to body so tests can find it
            container = document.createElement('div');
            container.id = 'item-list';
            container.setAttribute('data-virtual-list', '');
            document.body.appendChild(container);
        }
    }

    const processed = dedupeAndSort(items || []);
    if (!processed.length) {
        container.innerHTML = '<div class="empty-placeholder text-sm p-4">No items for selection.</div>';
        return;
    }

    // Build a table structure matching the server-rendered markup to avoid
    // a visual flash of unstyled, plain-text items. Keep a compatibility
    // class on rows ('.p-2' and '.virtual-item') so tests that look for those
    // selectors continue to work.
    const tableWrapper = document.createElement('div');
    tableWrapper.className = 'overflow-x-auto rounded-lg border border-base-300/80';

    const table = document.createElement('table');
    table.className = 'table table-zebra w-full';

    const thead = document.createElement('thead');
    thead.innerHTML = `
        <tr class="text-sm uppercase tracking-wide text-base-content/70">
            <th class="w-1/3">Item</th>
            <th class="w-1/3">Usage</th>
            <th class="w-1/6 text-right">Variants</th>
        </tr>
    `;

    const tbody = document.createElement('tbody');

    for (const i of processed) {
        const tr = document.createElement('tr');
        tr.className = 'p-2 virtual-item';
        tr.setAttribute('data-filter-item', '');
        tr.setAttribute('data-item-id', i.item_id || '');
        tr.setAttribute('data-item-name', i.name || '');
        tr.setAttribute('data-item-slot', (i.slot || 'Unknown').toLowerCase());

        // Item cell
        const tdItem = document.createElement('td');
        tdItem.className = 'align-top';
        const nameDiv = document.createElement('div');
        nameDiv.className = 'flex flex-col';
        const nameSpan = document.createElement('span');
        nameSpan.className = 'font-medium';
        nameSpan.textContent = i.name || '';
        const idSpan = document.createElement('span');
        idSpan.className = 'text-xs text-base-content/60';
        idSpan.textContent = i.item_id || '';
        nameDiv.appendChild(nameSpan);
        nameDiv.appendChild(idSpan);
        tdItem.appendChild(nameDiv);

        // Usage cell
        const tdUsage = document.createElement('td');
        tdUsage.className = 'align-top';
        const usageDiv = document.createElement('div');
        usageDiv.className = 'flex flex-col gap-1';
        const chipsDiv = document.createElement('div');
        chipsDiv.className = 'text-xs text-base-content/70';
        // Render per-context usage chips (i.usage_contexts expected as array of strings)
        if (Array.isArray(i.usage_contexts) && i.usage_contexts.length) {
            const preferred = ['main', 'follower', 'kanai'];
            // Sort contexts to ensure canonical display order: main, follower, kanai, others alphabetically
            const others = i.usage_contexts.filter(c => !preferred.includes(c)).sort();
            const ordered = [...preferred.filter(p => i.usage_contexts.includes(p)), ...others];
            for (const ctx of ordered) {
                const chip = document.createElement('span');
                chip.className = `usage-chip usage-${ctx}`;
                // Accessible: visible chip text should be announced by screen readers
                chip.textContent = ctx ? ctx.charAt(0).toUpperCase() + ctx.slice(1) : '';
                chipsDiv.appendChild(chip);
            }
        } else if (i.usage_label) {
            const label = document.createElement('span');
            label.className = 'text-xs text-base-content/70';
            label.textContent = i.usage_label || '';
            chipsDiv.appendChild(label);
        }
        usageDiv.appendChild(chipsDiv);
        tdUsage.appendChild(usageDiv);

        // Variants cell
        const tdVariants = document.createElement('td');
        tdVariants.className = 'align-top text-right text-sm';
        tdVariants.textContent = i.variant_ids && i.variant_ids.length ? String(i.variant_ids.length) : '—';

        tr.appendChild(tdItem);
        tr.appendChild(tdUsage);
        tr.appendChild(tdVariants);

        tbody.appendChild(tr);
    }

    table.appendChild(thead);
    table.appendChild(tbody);
    tableWrapper.appendChild(table);

    // Replace container contents with the new table wrapper
    container.innerHTML = '';
    container.appendChild(tableWrapper);
}

function collectSelectedBuildIds() {
    const select = document.querySelector('select[name="build_ids"]');
    if (!select) return [];
    return Array.from(select.selectedOptions).map(o => o.value);
}

// Use event delegation so dynamically-inserted controls (via HTMX) are handled
// without needing to re-bind listeners after swaps.
document.addEventListener('click', async (ev) => {
    const btn = ev.target && ev.target.closest && ev.target.closest('[data-testid="apply-filter-button"]');
    if (!btn) return;

    // Allow HTMX/normal submit to continue as well; this JS provides an immediate client-side
    // update to the item list for responsive UX.
    try {
        const buildIds = collectSelectedBuildIds();
        const payload = await fetchBuildItems(buildIds);
        renderItems(payload.data || []);
    } catch (err) {
        console.error('Item list fetch failed', err);
    }
});
