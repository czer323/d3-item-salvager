# Summary of errors observed while running `import-guides`

Overview

I scanned `logs/app.log` from the failed run of `uv run python -m d3_item_salvager import-guides` and summarised the most common error types. The run inserted 36 builds to the DB but encountered many parsing failures. The log is dominated by planner-profile HTTP 429 responses that prevented build profile resolution.

Top error categories (from logs)

1. Rate limiting when fetching planner profiles (HTTP 429) — ~98 occurrences
   - Concrete log examples:
     - "requests.exceptions.HTTPError: 429 Client Error: Too Many Requests for url: <https://planners.maxroll.gg/profiles/load/d3/{planner_id}>"
     - These are wrapped and re-raised as BuildProfileError in `d3_item_salvager.maxroll_parser.guide_profile_resolver`.
   - Symptom: "Failed to instantiate parser for guide %s" repeated many times.

2. BuildProfileError (raised when planner payload can't be loaded) — same set of occurrences as 429s
   - Message: "Failed to load planner profile {planner_id}: 429 Client Error: Too Many Requests..."
   - Source: `d3_item_salvager.maxroll_parser.maxroll_exceptions.BuildProfileError`.

3. Parser instantiation failures
   - Upstream effect: `BuildProfileParser` cannot be created because the resolver couldn't fetch planner data (due to 429s or missing data), generating noisy exception logs but no further detail on the parser internals.

Additional notes about log quality

- The logs show the exception type and message, but they don't include the guide URL or planner id in the top-level "Failed to instantiate parser for guide %s" message. The traceback contains the IDs, but the high-level error line would be more immediately useful if it included the failing guide URL/ID.
- There are many repeated identical error formats; the primary root cause is the server returning 429 responses during planner profile fetches.

Suggested immediate workarounds

- Retry the import with a slower request rate or with small batch sizes to avoid hitting rate limits.
- Use local reference data (development mode) by setting APP_ENV=development (or keeping `APP_USE_DOTENV=0`) so parser uses bundled JSON fixtures instead of the remote planner API.
- Add exponential backoff+retry logic for planner profile requests (short-term fix).

Recommended fixes (next steps)

1. Add robust retry/backoff for planner profile fetches (handle 429 with Retry-After header when present).
2. Implement batching and/or rate-limiting in the guide fetcher to keep request volume below the planner endpoint limits.
3. Improve log messages to include guide URL and planner id in the single-line error message emitted by the parser factory/log adapter.
4. Add an optional cache for planner profile payloads (persist to `cache/` directory) so repeated runs don't re-request the same planner ids.

File locations referenced

- `src/d3_item_salvager/maxroll_parser/guide_profile_resolver.py` — where planner payloads are requested and BuildProfileError is raised
- `src/d3_item_salvager/maxroll_parser/maxroll_exceptions.py` — BuildProfileError class
- `src/d3_item_salvager/services/build_guide_service.py` — wraps parser factory and logs instantiation failures

If you want, I can:

- Create a small patch that adds retry/backoff for planner profile requests (safe minimal change) and a test; or
- Implement a command-line flag to throttle requests (e.g., --rate=5 requests/sec) and wire it into the import task.

Short try-it steps

Run with local fixtures (fastest to reproduce success):

```bash
# Run import using development config and local reference files
APP_ENV=development APP_USE_DOTENV=0 uv run python -m d3_item_salvager import-guides
```

Or reduce request rate (if the CLI flag is added later):

```bash
# hypothetical example if rate limit flag is added
uv run python -m d3_item_salvager import-guides --rate 1
```

---
Generated on: 2025-10-11
