---
name: godot-gdscript-style
description: Apply this game jam project's GDScript 4.6 style rules — member naming, script member order, doc comments, @export annotation choices, shader uniform/sampler syntax, and RichTextLabel BBCode. Use whenever creating or editing a `.gd` script, a Godot shader, or GDScript doc comments and BBCode in this project, even without an explicit style request.
---

# Godot GDScript style

Engine: Godot 4.6. Language: GDScript.

## Rules

- Follow the naming convention and code order in `references/naming-and-order.md` in every `.gd` file.
- Write a doc comment (`##`) for every class, exported var, signal, enum, const, and public function — see `references/doc-comments.md`.
- Use static typing on every var, parameter, and return value.
- Never modify `.uid` and `.import` sidecars or the `.godot/` directory. Godot regenerates them.

## Reference files

| File | Topic |
|---|---|
| `references/naming-and-order.md` | Naming convention, script member order |
| `references/doc-comments.md` | Doc comment layout, BBCode and reference tags for doc comments |
| `references/exports.md` | All `@export` annotations, groups, dropdowns, numeric hints |
| `references/shaders.md` | Shader uniform syntax, sampler hints, setting parameters from GDScript |
| `references/bbcode-and-colors.md` | `RichTextLabel` BBCode tags, animated text effects, `[img]` options, named colors |

Read the reference file for the topic at hand before writing the code — don't guess at annotation syntax or tag names.
