# Diablo 3 Build Guide Item Scraper – Technical Requirements

## Project Overview

The goal of this project is to programmatically extract item data from Diablo 3 build guides hosted on <https://maxroll.gg/d3/category/guides> and build a comprehensive, queryable index of all build guides, with each variant/profile and all associated items, including their usage context (main, follower, Kanai’s Cube). This index will power a web UI for interactive queries and recommendations (e.g., what to keep, what to salvage, what to use for Kanai/follower), and can be used for further analysis or integration into other tools.

## Objectives

- Scrape the list of available build guides from the Maxroll Diablo 3 guides page.
- For each build guide and each variant/profile, extract:
  - Build Guide Title
  - Build Guide URL
  - Build Variant/Profile Name (if applicable)
  - Class (e.g., Barbarian, Wizard, etc.)
  - Item ID
  - Item Name
  - Slot (e.g., neck, ring, weapon, etc.)
  - Usage Context (main, follower, kanai)
- Store the extracted data in a structured, queryable format (e.g., CSV, JSON, or database) suitable for powering a web UI and supporting advanced queries.

## Data Schema

| Field              | Description                                 |
|--------------------|---------------------------------------------|
| build_guide_title  | Title of the build guide                    |
| build_guide_url    | URL of the build guide                      |
| build_variant      | Variant/profile name (if applicable, unique per guide/profile) |
| class_name         | Character class for the build               |
| item_id            | Unique item identifier (from master item list) |
| item_name          | Name of the item                            |
| slot               | Equipment slot (e.g., neck, ring, weapon)   |
| usage_context      | How the item is used (main, follower, kanai); one row per item/context/build/profile |
| set_status         | Set/Legendary status (if available)         |
| notes              | Additional notes (if available)             |

Each build variant/profile is uniquely identified by its name or key in the build profile JSON. Items that appear in multiple usage contexts or builds are represented by multiple rows, each with the correct context and build/profile linkage. Additional metadata such as set/legendary status and notes are included if present in the master item list.

## Scraping Approach

1. **Scrape Build Guide List**
   - Use the Maxroll Meilisearch API endpoint: `https://meilisearch-proxy.maxroll.gg/indexes/wp_posts_1/search` to fetch all build guides.
   - Send POST requests with a JSON body specifying `limit` and `offset` for pagination, and an empty query string to fetch all results.
   - The API requires a Bearer token in the Authorization header (extracted from browser network traffic).
   - For each response, parse the `hits` array and filter for entries where the `permalink` starts with `https://maxroll.gg/d3/guides/`.
   - For each valid hit, extract the build guide title (from the URL slug, or from a title field if available) and the guide URL.
   - Increment the `offset` by `limit` and repeat until fewer results than `limit` are returned, ensuring the full list is retrieved.

2. **Scrape Individual Build Guides and Build the Index**

   - For each build guide URL:
     - Parse the HTML to extract all `data-d3planner-id` attributes from `d3planner-build` divs (handle multiple IDs per page).
     - Fetch the build profile JSON from `https://planners.maxroll.gg/profiles/load/d3/{d3planner-id}`.
     - The build profile JSON contains all variants/profiles for the build, each with equipped items, cube items, and other data.
     - For each profile/variant (identified by name/key):
       - For each equipped item, follower item, and Kanai's Cube item:
         - Correlate the item ID with the master item list (from `reference/data.json` or `https://assets-ng.maxroll.gg/d3planner/data.json`).
         - Extract slot, item name, set/legendary status, notes, and other relevant fields.
         - Record the build guide title, URL, build variant/profile name, class, item ID, item name, slot, usage context (main, follower, kanai), and metadata.
     - Guides that reference the same d3planner profile ID are recorded separately, always linking the guide URL/title to each profile.
     - Items that appear in multiple usage contexts or builds are represented by multiple rows, each with the correct context and linkage.
   - This approach ensures a comprehensive, queryable index of all items in all builds, with full context and metadata.
   - If the API or HTML structure changes or becomes unavailable, fallback to cached/reference HTML/JSON files or switch to scraping rendered HTML. Implement error handling and anti-bot fallback strategies (e.g., user agent rotation, delays, proxies).

3. **Data Storage and Query Support**

   - Store the results in a structured, queryable format (CSV, JSON, or database). For small/medium datasets, CSV/JSON is sufficient; for large/complex queries, use SQLite or similar.
   - Ensure no duplicate entries. Each row is uniquely identified by build guide, variant/profile, item, and usage context.
   - Structure the data to support efficient queries by class, build, slot, usage context, set/legendary status, and notes.

## Query and Filter Logic

The backend or data export logic supports filtering the item index by class, build, slot, usage context, set/legendary status, and notes. The data format is designed for efficient queries and is suitable for powering a web UI or API. Example queries include:

- All items for a given class (e.g., Necromancer)
- All items for a specific build or variant
- All items used as Kanai's Cube powers
- All items used by followers
- All items to keep or salvage based on user preferences
- All items with set/legendary status

## Web UI Requirements

The web UI allows users to:

- Select a class and one or more builds/variants
- Optionally mark items as 'owned', 'ignore', or 'always keep' (stored in local storage for MVP; backend persistence may be added later)
- View a filtered, grouped list of items with usage context (main, follower, kanai), grouped by item and displaying all usage contexts
- Get recommendations for what to keep, what to salvage, what to use for Kanai/follower
- Filter by slot, set/legendary status, and notes
- Save user preferences (future enhancement)

## Recommended Tools & Libraries

- **requests**: For making HTTP requests
- **beautifulsoup4**: For parsing and navigating HTML
- **cloudscraper**: For bypassing anti-bot protections if needed
- **pandas**: For data manipulation and export (optional, for CSV/Excel output)
- **re**: For regular expressions (if needed for parsing)

## Anti-Bot Considerations

- The site may use anti-bot measures (e.g., Cloudflare). If requests are blocked, use `cloudscraper` as a drop-in replacement for `requests`.
- Consider adding random delays and user-agent rotation to mimic human browsing.

## Resources to Gather Ahead of Time

- Reference HTML files for:
  - List of builds (`reference/list_of_builds.html`)
  - Example build guide (`reference/build_guide.html`)
- List of all possible slot types (can be extracted from a sample build guide)
- List of all Diablo 3 classes (for mapping class names)
- Output format specification (CSV, JSON, or database schema)
- Legal review of scraping terms of service (ensure compliance with Maxroll's policies)

## Implementation Steps

1. Set up the project environment and dependencies
2. Implement build guide list scraper
3. Implement build guide item scraper
4. Implement data storage/export logic
5. Add error handling and anti-bot measures
6. Test with provided reference HTML files
7. Document usage and configuration

## Future Enhancements

- Add support for incremental updates by tracking last scrape date and comparing guide timestamps or diffs
- Add CLI or web interface for user interaction
- Integrate with other Diablo 3 tools or databases using compatible APIs/data formats
- Support user-defined item ignore/keep lists and persistent user settings (local storage for MVP, backend for advanced features)
- Ensure compliance with Maxroll's terms of service and document legal/ethical considerations
- Implement schema versioning and migration tools for index evolution

---

*This document serves as the initial technical requirements and implementation plan for the Diablo 3 Build Guide Item Scraper project.*

## Todo List

- Refactor the data schema and export logic to include usage context and item IDs, and ensure one row per item per profile/variant.
- Implement the index-building logic to emit a comprehensive, queryable table of all items in all builds, with usage context.
- Implement query/filter logic to support filtering by class, build, slot, and usage context.
- Design and build the web UI for interactive queries and recommendations.
- Add support for user-defined item ignore/keep lists and persistent user settings.
- Test with provided reference HTML files and real data.
- Document usage, configuration, and extensibility.
