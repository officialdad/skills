# @export

Put a `##` doc comment above each `@export` var. The comment becomes the inspector tooltip.

| Need | Annotation |
|---|---|
| Multiline text | `@export_multiline("monospace", "no_wrap")` |
| Placeholder text | `@export_placeholder("text when empty")` |
| Any file path | `@export_file("*.txt")` |
| `res://` path | `@export_file_path("*.txt")` |
| `res://` UID | `@export_global_file("*.txt")` |
| Number range | `@export_range(min, max, step, "hint")` |
| Soft range | `@export_range(..., "or_greater", "or_less")` |
| Unit suffix | `@export_range(..., "suffix:coins")` |
| Degrees | `@export_range(..., "degrees")` |
| Radians shown as degrees | `@export_range(..., "radians_as_degrees")` |
| Ease curve | `@export_exp_easing` |
| Linked Vector2/3/4 ratio | `@export_custom(PROPERTY_HINT_LINK, "")` |
| Real enum | `@export var x: Letters` |
| String dropdown | `@export_enum("a", "b") var option: String` |
| Int dropdown with values | `@export_enum("slow:1", "normal:5", "fast:9") var speed: int = 5` |
| Dropdown plus free entry | `@export_custom(PROPERTY_HINT_ENUM_SUGGESTION, "a,b")` |
| Input action name | `@export_custom(PROPERTY_HINT_INPUT_NAME, "")` |
| Group | `@export_group("Title")` |
| Group with prefix hidden | `@export_group("Title", "cool_")` |
| Subgroup | `@export_subgroup("Title")` |
| Category (class inheritance) | `@export_category("Title")` |
| Toggle group | `@export_custom(PROPERTY_HINT_GROUP_ENABLE, "")` on a `bool` var, inside a group |

Notes:

- A group runs until the next `@export_group` or `@export_subgroup`.
- `@export_enum` on an `int` without values stores the index.
- A slider with `or_greater` or `or_less` still accepts typed values outside the range.
- `radians_as_degrees` shows degrees and stores radians.
- Typed arrays work: `Array[float]`, `Array[String]`.
