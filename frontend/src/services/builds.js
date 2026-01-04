// Minimal builds service (T011)
// Expose a small helper to fetch union items for selected build ids.

export async function fetchBuildItems(buildIds = [], { limit = 100, offset = 0 } = {}) {
    const params = new URLSearchParams();
    params.set('build_ids', buildIds.join(','));
    params.set('limit', String(limit));
    params.set('offset', String(offset));

    const res = await fetch(`/builds/items?${params.toString()}`, {
        headers: { 'Accept': 'application/json' },
    });
    if (!res.ok) {
        throw new Error(`Failed to fetch build items: ${res.status}`);
    }
    return res.json();
}
