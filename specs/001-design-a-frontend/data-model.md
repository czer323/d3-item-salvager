# data-model.md

## Entities

Derived from feature spec `spec.md`.

- BuildGuide
  - id: string
  - title: string
  - url: string | null
  - class_name: string (one of: 'barbarian', 'wizard', 'necromancer', ...; see backend enum)
  - last_updated: ISO8601 timestamp

- Variant
  - id: string
  - name: string
  - build_guide_id: string
  - items: list[ItemUsage] (references)
*Note: All Variant fields are required. References to BuildGuide are not nullable.*

- Item
  - id: string
  - name: string (required)
  - slot: string (e.g., Helm, Chest, Ring)
  - set_status: string | null (e.g., 'set', 'unique')
  - notes: string | null

- ItemUsage
  - item_id: string
  - variant_id: string
  - usage_context: enum('main','follower','kanai') (main: primary build; follower: follower build; kanai: Kanai's Cube)

  *Note: `item_id` and `variant_id` are required. Deletion of referenced Item or Variant should [cascade/soft-delete/TBD].*

- Preferences
  - selected_class_ids: list[string]
  - selected_build_ids: list[string]
  - selected_variant_ids: list[string]

  *Note: Preferences are [per-user/per-session]. All list fields may be empty. Relationship to BuildGuide and Variant IDs should be enforced at the application layer.*  *Note: Preferences are [per-user/per-session]. All list fields may be empty. Relationship to BuildGuide and Variant IDs should be enforced at the application layer.*  - selected_variant_ids: list[string]

## Validation rules and referential integrity

This section documents the validation constraints the backend enforces, the referential integrity policies for relations, expected cascade/soft-delete behaviour, and the standard error codes/messages the API returns so the frontend can implement consistent handling.

1) Backend-enforced constraints
- BuildGuide
  - `title`: required, non-empty string (trimmed). Backend rejects empty or whitespace-only titles with 400 (validation_error).
  - `url`: optional; if provided, must be a well-formed URL.
  - `class_name`: must be one of the canonical class labels maintained by the backend (Title Case: `Barbarian`, `Crusader`, `Demon Hunter`, ...). Invalid values return 400 (validation_error).
- Variant / Profile
  - `name`: required, non-empty.
  - `build_guide_id`: required and must reference an existing BuildGuide; invalid or missing references return 400 / 404 as appropriate.
  - `items` (list of ItemUsage entries) may be empty.
- Item
  - `name`: required, non-empty.
  - `slot`: required; must be one of the backend-managed slot values (e.g., `head`, `mainhand`, `offhand`, `jewelry`, ...). Invalid slot values return 400 (validation_error).
  - `set_status`: optional, constrained to allowed values (e.g., `set`, `legendary`, `unique`).
- ItemUsage
  - `item_id` and `variant_id`: required, must reference existing Item and Variant respectively. Creation of usages referencing missing resources returns 400 (validation_error) or 404 (not_found) with a clear code.

2) Referential integrity policies
- Database-level referential constraints are preferred where practical (foreign keys with enforced referential integrity). The application also validates references at the API layer.
- Deletion rules:
  - BuildGuide: **deletion is disallowed** while Variants exist; attempting to delete returns 409 (resource_conflict) with message `Cannot delete build: variants exist`.
  - Variant: **cascade delete** ItemUsage entries (so removing a variant removes its usages). API deletion returns 204 No Content on success.
  - Item: **soft-delete** (recommended) — items have a `deleted` flag. Soft deleting an Item preserves historical ItemUsage rows and surfaces to clients as `Item not available`. Attempts to hard-delete an Item that still has usages should return 409 (resource_conflict) unless force-delete is explicitly requested and documented.
- Creation/update behaviour:
  - Attempts to create or update records with missing/invalid foreign keys are rejected with 400 (validation_error) and `code: "fk_violation"` in the JSON body when the problem is reference-related.

3) Cascade/soft-delete behaviour and client UI fallbacks
- Soft-deleted Items: APIs return the item record but include `available: false` (or `deleted: true`) so the frontend can show a consistent fallback state: display `Item not available` and disable interactions (e.g., cannot apply to current selection).
- Missing builds for selected classes: API should return an empty builds list for that class; frontend displays `No builds found` in the builds selector and preserves the selected class.
- Missing variants: UI displays `No variants found` in the variants area.
- Unavailable associated resources (e.g., ItemUsage referencing a soft-deleted Item): show `Item not available` in place of the item name and include a tooltip or action to `View item history` where applicable.

4) Validation points, background integrity checks, and sample error codes/messages
- Where to validate:
  - Request boundary: all create/update endpoints MUST validate payload shape, field constraints, and foreign key existence.
  - Background/periodic checks: scheduled worker should run integrity checks (e.g., orphaned ItemUsage rows, profiles referencing missing builds) and report/fix or alert (logs, metrics).
- Sample error response conventions (JSON):
  - 400 Bad Request — validation errors
    - {
      "code": "validation_error",
      "message": "BuildGuide.title is required and must not be empty",
      "details": {"title": "required"}
    }
  - 404 Not Found — resource not found
    - {
      "code": "not_found",
      "message": "BuildGuide not found",
    }
  - 409 Conflict — referential or business conflict
    - {
      "code": "resource_conflict",
      "message": "Cannot delete build: variants exist",
    }
  - 422 Unprocessable Entity — optional (if using more granular semantics for semantic errors)
- Frontend guidance for handling errors:
  - Validation (400): surface field-level messages inline and show toast with the `message` for user correction.
  - Not found (404): show a user-friendly message and enable a refresh/retry flow; for list endpoints treat as empty list and show `No results`.
  - Conflict (409): show an explanatory modal with next steps (e.g., remove dependent records first or contact admin).

These rules ensure consistent behavior between API and UI, make error handling predictable, and provide guidance for integrity maintenance and client fallbacks.

## State transitions

- Preferences: saved -> exported -> imported
- UI selection: selection changes trigger re-render (HTMX partial updates)
