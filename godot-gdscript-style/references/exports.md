# @export

Sources: the [exports tutorial](https://docs.godotengine.org/en/4.7/tutorials/scripting/gdscript/gdscript_exports.html) and the [`@GDScript` class reference](https://docs.godotengine.org/en/4.7/classes/class_@gdscript.html), Godot 4.7.

Put a `##` doc comment directly above each `@export` var. The comment becomes the inspector tooltip. A `##` block documents only the member directly under it.

## Text and paths

| Need | Annotation |
|---|---|
| Multiline text | `@export_multiline("monospace", "no_wrap")` |
| Placeholder text | `@export_placeholder("text when empty")` |
| Project file, stored as a UID when one exists | `@export_file("*.txt")` |
| Project file, stored as a raw `res://` path | `@export_file_path("*.txt")` |
| Absolute file path, any folder on disk | `@export_global_file("*.txt")` |
| Project directory | `@export_dir` |
| Absolute directory path, any folder on disk | `@export_global_dir` |
| Node path filtered by type | `@export_node_path("Button", "TouchScreenButton")` |

## Numbers and colors

| Need | Annotation |
|---|---|
| Number range | `@export_range(min, max, step, "hint")` |
| Soft range | `@export_range(..., "or_greater", "or_less")` |
| Exponential range | `@export_range(..., "exp")` |
| Slider on an `int` | `@export_range(..., "prefer_slider")` |
| Hide the slider | `@export_range(..., "hide_control")` |
| Unit suffix | `@export_range(..., "suffix:coins")` |
| Degrees | `@export_range(..., "degrees")` |
| Radians shown as degrees | `@export_range(..., "radians_as_degrees")` |
| Ease curve | `@export_exp_easing`, `@export_exp_easing("attenuation")`, `@export_exp_easing("positive_only")` |
| Linked Vector2/3/4 ratio | `@export_custom(PROPERTY_HINT_LINK, "")`. A hint such as `"suffix:px"` is valid. |
| Color with no alpha | `@export_color_no_alpha` |

## Choices and flags

| Need | Annotation |
|---|---|
| Real enum | `@export var x: Letters` |
| String dropdown | `@export_enum("a", "b") var option: String` |
| Int dropdown with values | `@export_enum("slow:1", "normal:5", "fast:9") var speed: int = 5` |
| Dropdown plus free entry | `@export_custom(PROPERTY_HINT_ENUM_SUGGESTION, "a,b")` |
| Input action name | `@export_custom(PROPERTY_HINT_INPUT_NAME, "")`. Hints: `"show_builtin"`, `"loose_mode"`. |
| Bit flags | `@export_flags("Fire", "Water", "Earth")`, explicit values `@export_flags("Self:4", "Allies:8")` |
| 2D layer bits | `@export_flags_2d_render`, `@export_flags_2d_physics`, `@export_flags_2d_navigation` |
| 3D layer bits | `@export_flags_3d_render`, `@export_flags_3d_physics`, `@export_flags_3d_navigation` |
| Avoidance layer bits | `@export_flags_avoidance` |

## Groups and storage

| Need | Annotation |
|---|---|
| Group | `@export_group("Title")` |
| Group limited to a prefix, prefix hidden | `@export_group("Title", "cool_")` |
| End a group | `@export_group("", "")` |
| Subgroup | `@export_subgroup("Title")`. Nest with a slash: `"Wheels/Front"`. |
| Category (class inheritance) | `@export_category("Title")` |
| Toggle group | `@export_custom(PROPERTY_HINT_GROUP_ENABLE, "")` on a `bool` var, inside a group or subgroup. Hint: `"checkbox_only"`. |
| Saved, hidden from the inspector | `@export_storage` |
| Editor button that calls a `Callable` | `@export_tool_button("Text", "Icon")`. The script needs `@tool`. |
| Any hint and usage pair | `@export_custom(hint, "hint_string", usage)` |
| Plain | `@export` |

## Notes

- A group runs until the next `@export_group` or `@export_category`. A subgroup nests inside the current group.
- A group with a prefix also ends at the first property that lacks the prefix.
- `@export_enum` on an `int` without values stores the index.
- A slider with `or_greater` or `or_less` still accepts typed values outside the range.
- `radians_as_degrees` shows degrees and stores radians.
- Typed arrays work: `Array[float]`, `Array[String]`. Packed arrays work only when initialised empty.
- Never add `@export_enum` for an id whose valid values live in `data/*.json`, such as `hero_id`, `encounter`, or `start_anim`. Keep the data out of code.
