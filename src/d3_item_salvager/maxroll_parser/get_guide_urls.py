import json

import requests

# Meilisearch API endpoint and Bearer token for fetching all builds
MEILISEARCH_URL = "https://meilisearch-proxy.maxroll.gg/indexes/wp_posts_1/search"
MEILISEARCH_BEARER = "35679298edc476d0b9f9638cdb90d362235a62550bea39d59544f694cc9d90b9"


def fetch_all_guides_meilisearch(limit: int = 21) -> list[dict[str, str]]:
    """Fetches all Diablo 3 build guides from Maxroll's Meilisearch API with pagination.

    Args:
        limit: Number of results per page (default 21, as used by the site).

    Returns:
        List of dictionaries with 'name' and 'url' keys.
    """
    headers = {
        "accept": "*/*",
        "authorization": f"Bearer {MEILISEARCH_BEARER}",
        "content-type": "application/json",
    }
    offset = 0
    all_guides = []
    seen_urls = set()
    debug_printed = 0
    while True:
        body = {"q": "", "facets": [], "limit": limit, "offset": offset}
        resp = requests.post(
            MEILISEARCH_URL, headers=headers, data=json.dumps(body), timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        hits = data.get("hits", [])
        if not hits:
            break
        # Print a few sample hits for inspection
        if debug_printed < 5:
            print("\n--- Sample hit(s) from Meilisearch API ---")
            for i, hit in enumerate(hits[:3]):
                print(f"Hit {i + 1}: {json.dumps(hit, indent=2)[:500]}...\n")
            debug_printed += 1
        for hit in hits:
            url = hit.get("permalink", "")
            if url.startswith("https://maxroll.gg/d3/guides/") and url not in seen_urls:
                # Extract build slug from URL
                build_slug = url.split("/d3/guides/")[-1].strip("/")
                # Convert slug to readable name
                name = build_slug.replace("-", " ").replace("guide", "Guide").strip()
                name = " ".join(
                    [w.capitalize() if w != "Guide" else w for w in name.split()]
                )
                all_guides.append({"name": name, "url": url})
                seen_urls.add(url)
        if len(hits) < limit:
            break
        offset += limit
    return all_guides


def main() -> None:
    """Fetches and prints deduplicated build guide names and URLs."""
    # Use Meilisearch API for full list; fallback to HTML if needed
    guides = fetch_all_guides_meilisearch()
    for guide in guides:
        print(f"{guide['name']}: {guide['url']}")
    print(f"\nTotal guides found: {len(guides)}")


if __name__ == "__main__":
    main()
