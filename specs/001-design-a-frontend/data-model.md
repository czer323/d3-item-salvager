# data-model.md

## Entities

Derived from feature spec `spec.md`.

- BuildGuide
  - id: string
  - title: string
  - url: string (optional)
  - class_name: string
  - last_updated: ISO8601 timestamp

- Variant
  - id: string
  - name: string
  - build_guide_id: string
  - items: list[ItemUsage] (references)

- Item
  - id: string
  - name: string
  - slot: string (e.g., Helm, Chest, Ring)
  - set_status: string | null (e.g., 'set', 'unique')
  - notes: string | null

- ItemUsage
  - item_id: string
  - variant_id: string
  - usage_context: enum('main','follower','kanai')

- Preferences
  - selected_class_ids: list[string]
  - selected_build_ids: list[string]
  - selected_variant_ids: list[string]

## Validation rules

- `BuildGuide.title` is required and non-empty.
- `Variant.items` may be empty; when empty the UI shows 'No items found'.
- `Item.name` is required; `Item.slot` must be one of the known slots set by the backend.

## State transitions

- Preferences: saved -> exported -> imported
- UI selection: selection changes trigger re-render (HTMX partial updates)
