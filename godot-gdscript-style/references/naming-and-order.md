# Naming convention and code order

Source: the [Godot 4.7 GDScript style guide](https://docs.godotengine.org/en/4.7/tutorials/scripting/gdscript/gdscript_styleguide.html).

## Naming

| Item | Style | Example |
|---|---|---|
| File | snake_case of the `class_name` | `cool_script.gd` holds `class_name CoolScript` |
| Class | PascalCase | `class_name CoolScript` |
| Node | PascalCase | `$AnimatedSprite2D` |
| Function | snake_case | `func load_level() -> void:` |
| Variable | snake_case | `var particle_effect: Node3D` |
| Private function or variable | `_` then snake_case | `var _counter: int = 0` |
| Signal | snake_case, past tense | `signal door_opened` |
| Constant | CONSTANT_CASE | `const MAX_SPEED: float = 200.0` |
| Class loaded into a constant | PascalCase | `const Weapon = preload("res://weapon.gd")` |
| Enum | PascalCase | `enum CoolElement` |
| Enum member | CONSTANT_CASE | `EARTH,` |

### File name exceptions

These 6 files keep a class name that adds the directory as a prefix. Never rename them.

| File | Class |
|---|---|
| `src/game/combat/stage/draw.gd` | `StageDraw` |
| `src/game/combat/stage/locomotion.gd` | `StageLocomotion` |
| `src/game/combat/stage/reactions.gd` | `StageReactions` |
| `src/game/combat/stage/ring.gd` | `StageRing` |
| `src/game/spike/village.gd` | `SpikeVillage` |
| `src/sim/bots.gd` | `SimBots` |

## Enum layout

Write each item on its own line. End the last item with a comma. `gdformat` collapses an enum with no trailing comma onto one line.

```gdscript
enum Element {
	EARTH,
	WATER,
}
```

## Code order

Top to bottom in each script:

1. `@tool`, `@icon`, `@static_unload`
2. `class_name`
3. `extends`
4. `##` doc comment
5. `signal`
6. `enum`
7. `const`
8. `static var`
9. `@export var`
10. `var`
11. `@onready var`
12. `_static_init()`
13. Remaining static functions
14. Overridden built-in virtual functions, in this order: `_init`, `_enter_tree`, `_ready`, `_process`, `_physics_process`, remaining virtual functions
15. Overridden custom functions
16. Remaining functions
17. Inner classes

Inside each step, put public members first and private members second.

## Safe member moves

GDScript runs member initialisers in declaration order. A move can change a value.

- Read each initialiser of a moved `var` or `static var`. Keep it below every member it reads.
- Move a `##` block and its member as one unit. The block must sit directly above the member or its annotations, with no blank line.
- Run `tools/test.sh` after each reorder.
