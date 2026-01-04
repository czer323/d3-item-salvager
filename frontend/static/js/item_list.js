// Client-side wiring to fetch /builds/items and render into #item-list (T011)

async function fetchBuildItems(buildIds = [], { limit = 100, offset = 0 } = {}) {
  const params = new URLSearchParams();
  params.set('build_ids', buildIds.join(','));
  params.set('limit', String(limit));
  params.set('offset', String(offset));

  const res = await fetch(`/builds/items?${params.toString()}`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!res.ok) throw new Error('Failed to fetch build items');
  return res.json();
}

function dedupeAndSort(items = []) {
  const seen = new Set();
  const unique = [];
  for (const it of items) {
    const key = String(it.id ?? it.name ?? '');
    if (seen.has(key)) continue;
    seen.add(key);
    unique.push(it);
  }
  unique.sort((a, b) => (a.name || '').localeCompare(b.name || ''));
  return unique;
}

function renderItems(items) {
  const container = document.querySelector('#item-list');
  if (!container) return;
  const processed = dedupeAndSort(items || []);
  if (!processed.length) {
    container.innerHTML = '<div class="empty-placeholder text-sm p-4">No items for selection.</div>';
    return;
  }
  const list = processed.map(i => `<div class="p-2 border-b">${i.name} <span class="text-xs text-base-content/60">(${i.slot})</span></div>`).join('');
  container.innerHTML = list;
}

function collectSelectedBuildIds() {
  const select = document.querySelector('select[name="build_ids"]');
  if (!select) return [];
  return Array.from(select.selectedOptions).map(o => o.value);
}

document.addEventListener('DOMContentLoaded', () => {
  const applyBtn = document.querySelector('[data-testid="apply-filter-button"]');
  if (!applyBtn) return;

  applyBtn.addEventListener('click', async (ev) => {
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
});
