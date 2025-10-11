# Remote Maxroll Integration

**Related Issue**: n/a – aligns with original implementation plan

## Goal

Enable the production workflow to ingest live Diablo 3 build guides from Maxroll by fetching guide listings, resolving planner profiles, and populating the local database with parsed builds/items.

## High-Level Plan

1. Extend configuration to capture all remote endpoints (guide search, planner profile loader) and runtime options such as HTTP user agent/timeouts.
2. Introduce a resolver that derives planner profile IDs for a guide (via HTML parsing or API metadata) and fetches the associated profile JSON from the planner service.
3. Update build profile parsing to combine multiple planner payloads per guide and surface consolidated profile/item data.
4. Wire the new resolver into `BuildGuideService` and `MaxrollClient` so that the service processes remote guides end-to-end.
5. Add regression tests using fixture data/mocked HTTP responses and run the project checks.

## Public API Changes

- `MaxrollParserConfig`: new fields for planner profile URL template and HTTP configuration.
- `BuildProfileParser` constructor will accept optional parser configuration (backwards compatible default).
- `GuideInfo` remains stable; downstream services consume updated parser behavior transparently.

## Testing Plan

- Unit tests for the planner resolver covering HTML extraction and error cases (using saved HTML fixtures).
- Unit tests for `BuildProfileParser` combining multiple planner payloads (mocked requests).
- Service-level test exercising `BuildGuideService.build_profiles_from_guides` with mocked network layer.
- Run `uv run pre-commit run --all-files` (or component commands) locally to cover linting, typing, and tests.

## Implementation Steps

- [ ] Add new configuration fields/constants for planner profile fetching and default headers/timeouts.
- [ ] Implement a guide profile resolver (HTML parser + planner fetcher) and expose it for reuse.
- [ ] Update `BuildProfileParser` to use the resolver, aggregate planner data, and accept optional config.
- [ ] Adjust `BuildGuideService`/`MaxrollClient` to inject config and work with the enhanced parser.
- [ ] Create/update tests with fixtures/mocks validating the new behavior.
- [ ] Execute `uv run pre-commit run --all-files` (or equivalent) and address any failures.

## Deviations

- None at this time.
