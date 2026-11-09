---
name: godot-gdscript-style
description: Apply the GDScript style rules of project-d20, a 3D cel-shaded game on Godot 4.7. Covers member naming, script member order, doc comments, line length, @export annotation choices, shader uniform and sampler syntax, and RichTextLabel BBCode. Use whenever creating or editing a `.gd` script, a Godot shader, or GDScript doc comments in this project, even without an explicit style request.
---

# Godot GDScript style

Engine: Godot 4.7 (project pin 4.7.2). Language: GDScript.

## Rules

- Follow the naming convention and code order in `references/naming-and-order.md` in every `.gd` file.
- Put public members before private members inside each step of the code order. A private member starts with `_`.
- Write each enum item on its own line, with a trailing comma after the last item.
- Keep each line at 100 columns or fewer. Count a tab as 4 columns.
- Name a new script file as the snake_case of its `class_name`. Leave the 6 listed exceptions in `references/naming-and-order.md` as they are.
- Write a `##` doc comment for every class, inner class, exported var, signal, enum, const, and public function. See `references/doc-comments.md`.
- In `tests/`, write the script-level `##` only. Skip `##` on test functions, helpers, and constants.
- Use a `//` comment above a shader uniform whose unit, range, or color space is not clear from its name. Never require `/** */` on a uniform.
- Use static typing on every var, parameter, return value, and `for` variable.
- Never modify `.uid` and `.import` sidecars or the `.godot/` directory. Godot regenerates them.
- Run `gdlint` on each `.gd` file you edit once the project has a `gdlintrc`. Fix every report it prints.

The decisions behind these rules, their evidence, and their enforcers are in `references/decisions.md`.

## Reference files

| File | Topic |
|---|---|
| `references/naming-and-order.md` | Naming convention, script member order, safe member moves |
| `references/doc-comments.md` | Doc comment layout, BBCode and reference tags for doc comments |
| `references/exports.md` | All 27 `@export` annotations, groups, dropdowns, numeric hints |
| `references/shaders.md` | Shader uniform syntax, sampler hints, setting parameters from GDScript |
| `references/bbcode-and-colors.md` | `RichTextLabel` BBCode tags, animated text effects, `[img]` options, named colors. No project code uses it today. |
| `references/decisions.md` | The four standards decisions, their reasons, and their enforcers |

Read the reference file for the topic at hand before writing the code. Never guess at annotation syntax or tag names.
