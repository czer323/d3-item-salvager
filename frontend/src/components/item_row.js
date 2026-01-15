// Minimal client-side helpers for item rows (T018)
export function createItemRow(item) {
    const root = document.createElement('div');
    root.className = 'item-row';
    root.setAttribute('data-item-id', item.id);

    const name = document.createElement('span');
    // Sanitise quality text to a safe CSS class token (lowercase, hyphenated, alphanum)
    const qualityCls = String(item.quality || '')
        .toLowerCase()
        .replace(/\s+/g, '-')
        .replace(/[^a-z0-9-]/g, '') || 'unknown';
    name.className = `item-name quality-${qualityCls}`;
    // Sanitize visible name to remove internal tokens like P4_ or Unique_ and convert underscores
    const sanitizeName = (s) => String(s || '')
        .replace(/\bP\d+_/g, '')
        .replace(/\bUnique_/gi, '')
        .replace(/_/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
    const visibleNameRaw = sanitizeName(item.name);
    const fallbackName = visibleNameRaw || String(item.name || 'Unnamed Item');
    const qualityLabel = String(item.quality || '');
    name.setAttribute('aria-label', `Item: ${fallbackName}, ${qualityLabel}`);
    name.textContent = fallbackName;

    const slot = document.createElement('div');
    slot.className = 'item-slot';
    slot.textContent = item.slot || '';

    const usages = document.createElement('div');
    usages.className = 'usages';
    (item.usage_contexts || []).forEach((u) => {
        const chip = document.createElement('span');
        chip.className = 'usage-chip';
        chip.dataset.usage = u;
        chip.setAttribute('aria-hidden', 'true');
        chip.textContent = u;
        usages.appendChild(chip);
    });

    root.appendChild(name);
    root.appendChild(slot);
    root.appendChild(usages);
    return root;
}
