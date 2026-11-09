# Standards decisions

Date: 2026-11-09. Project: project-d20 at `fb1bced7`, Godot 4.7.2.
Evidence: the style audit of project-d20 (`d20-gdscript-style-audit-s1`), the Godot 4.7 docs, and a `gdlint` 4.5.0 run over the project.

Test for each call: Claude agents write and edit this game in every session. Agent reliability, small diffs, low behaviour risk, and a gate a tool can enforce outrank human taste.

## Summary

| Call | Decision | Project change |
|---|---|---|
| Doc comments in `tests/` | Script-level `##` only. Test functions, helpers, and constants are exempt. | Keep |
| Official rules the skill omitted | Adopt all three: public before private, one enum item per line, 100 columns. | Refactor batches |
| 6 class and file name mismatches | Stay as they are. New files follow the rule. | Keep |
| `/** */` on shader uniforms | Not required. `//` above a uniform that needs a note. | Keep |

## 1. Doc comments in `tests/`

Decision: in `tests/`, write the script-level `##` only. Skip `##` on test functions, helpers, and constants.

Reason:

- 266 of 266 scripts already carry a script-level `##`. 1545 of 1600 public functions in `tests/` have none.
- A `test_*` name states the behaviour under test, and the test runner finds it by that prefix. No reader opens editor help for a test function.
- Requiring `##` there adds about 1545 comment lines with no reader, and every new test grows the diff.

Enforcer: none exists. `gdlint` 4.5.0 has no doc comment check. The engine has no missing-doc warning.

## 2. Official style-guide rules the skill omitted

Decision: adopt all three rules from the [4.7 style guide](https://docs.godotengine.org/en/4.7/tutorials/scripting/gdscript/gdscript_styleguide.html).

### Public before private

The guide orders members "1. public 2. private" inside the code order. A private member starts with `_`.

- One fixed order lets an agent place a new member without judgement. Function order has no runtime effect.
- 36 files put a private function before a public one (155 functions). 13 files do the same for variables (43).
- Risk: a moved `var` can change value when its initialiser reads another member. Move vars only after reading each initialiser.

Enforcer:

- Variables: `gdlint` rule `class-definitions-order`. Its default order already puts `pubvars` before `prvvars` and `onreadypubvars` before `onreadyprvvars`. It reports 112 hits in 28 files of `src/` and `tools/` today.
- Functions: none exists. `gdlint` puts every function in one `others` bucket.

### One enum item per line

The guide: "Write enums with each item on its own line."

- 9 of 9 enums are single-line today. A single-line enum cannot carry a `##` per value.
- 9 enums change. Adding an item later is a one-line diff. No behaviour risk.

Enforcer: none flags a single-line enum. `gdformat` 4.5.0 keeps a multi-line enum with a trailing comma, and collapses one without a trailing comma onto one line. The skill requires the trailing comma for that reason.

### 100-column limit

The guide: "Keep individual lines of code under 100 characters."

- `gdlint` checks it with no extra code: `max-line-length: 100`. Set `tab-characters: 4` to count a tab as the editor shows it.
- Short lines keep a one-token edit to a small diff hunk.
- Cost: 4485 lines in `src/` and `tools/` pass 100 columns with `tab-characters: 4`. A wrap batch must land before the gate turns on. Until then, keep each new or edited line within the limit.
- This call was close. The wrap batch is large, but it has no behaviour risk and gives a tool-enforced gate.

Enforcer: `gdlint` rule `max-line-length`.

## 3. Class and file name mismatches

Decision: keep the 6 files as they are. Name every new file as the snake_case of its `class_name`.

| File | Class |
|---|---|
| `src/game/combat/stage/draw.gd` | `StageDraw` |
| `src/game/combat/stage/locomotion.gd` | `StageLocomotion` |
| `src/game/combat/stage/reactions.gd` | `StageReactions` |
| `src/game/combat/stage/ring.gd` | `StageRing` |
| `src/game/spike/village.gd` | `SpikeVillage` |
| `src/sim/bots.gd` | `SimBots` |

Reason:

- A file rename moves the `res://` path, the `.uid` sidecar, and every `preload`. The audit rates it medium risk and left 3 of the 6 paths unchecked.
- A class rename to `Draw`, `Ring`, or `Bots` puts generic names in the global class namespace.
- The directory already carries the prefix. An agent finds each class with one search for `class_name StageDraw`.

Enforcer: none exists. `gdlint` checks only the class name case. The engine has no file name warning.

## 4. `/** */` on shader uniforms

Decision: a uniform needs no `/** */` doc comment. Write a `//` comment above a uniform whose unit, range, or color space is not clear from its name.

Reason:

- `/** */` text shows only as an inspector tooltip. Every material in the project is built in code. No `.tres` or `.tscn` file holds a shader material, so no tooltip ever shows.
- 0 of 154 uniforms use `/** */`. 48 carry a `//` comment. An agent reads both forms the same way in the source.
- Converting 48 comments changes no behaviour and helps no reader.

Enforcer: none needed. No shader lint exists for Godot.

## Enforcer notes

- `gdtoolkit` 4.5.0 (2025-10-09) is the latest release. No release names Godot 4.6 or 4.7.
- `gdlint` 4.5.0 parses 260 of 266 project `.gd` files. The other 6 fail on a variable named `set`, for example `src/cel/ink_effect.gd:110`. `gdlint` reports the parse error and skips the file. Godot accepts the name.
- The typing rule has an engine gate: set `debug/gdscript/warnings/untyped_declaration` to Error in `project.godot`. Typing is already clean except 8 `for` variables in `src/` and `tools/`, so type them first.
- Project config changes belong to the refactor task, not this skill.
