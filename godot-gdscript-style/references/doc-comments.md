# Doc comments

Source: [GDScript documentation comments, Godot 4.7](https://docs.godotengine.org/en/4.7/tutorials/scripting/gdscript/gdscript_documentation_comments.html).

Write a `##` doc comment for every class, inner class, exported var, signal, enum, const, and public function. Use static typing on every var, parameter, and return value.

In `tests/`, write the script-level `##` only. Skip `##` on test functions, helpers, and constants. See `decisions.md`.

```gdscript
class_name ExampleClass
extends Node
## Class role (short).
##
## Script description and details (long).
## Use [br] to keep new lines separated.
##
## @tutorial(text shown): url
## @experimental

enum Animal { ## Inline description.
	DOG, ## Adult puppy.
	CAT, ## Adult kitty.
}

## Description of var, signal, const, or enum.
var player_speed: float = 50.0


## [b]Heals[/b] [Player] by [param amount].
func add_coolness_point(amount: int) -> void:
	pass
```

- Put the `##` block directly above the member or its annotations. A blank line detaches it.
- Write `[br]` at the end of each list line. The editor joins plain `##` lines into one paragraph.
- Write `[lb]` and `[rb]` for a literal `[` and `]`.
- Write `[code]` for inline code. Never use Markdown backticks.
- Put `[b]Note:[/b]` or `[b]Warning:[/b]` at the end of a doc comment, after a `[br]`.
- Put `@deprecated:` or `@experimental:` at the very end of a doc comment. Text after the tag is optional.

## Doc comment BBCode

| Purpose | Tag |
|---|---|
| Bold, italic, underline, strike | `[b]` `[i]` `[u]` `[s]` |
| Centered text | `[center]` |
| Hyperlink | `[url=LINK]text[/url]` |
| Keyboard shortcut | `[kbd]` |
| Inline code | `[code]` |
| Code block | `[codeblock]`. Use 4 spaces, not tabs. |
| Literal brackets | `[lb]` `[rb]` |
| Line break | `[br]` |
| Image | `[img width= height=]PATH[/img]` |
| Color, font | `[color=COLOR]` `[font=PATH]`. Avoid both in doc comments. |

Reference tags link to other classes and members. Omit the class name when the target is in the current class.

| Target | Tag |
|---|---|
| Class | `[Sprite2D]` |
| Signal | `[signal Button.pressed]` |
| Enum | `[enum Tween.EaseType]` |
| Constant | `[constant Color.BLUE]` |
| Member | `[member Node2D.modulate]` |
| Method | `[method print]` |
| Method parameter | `[param name]` |

Other reference tags: `annotation`, `constructor`, `operator`, `theme_item`.
