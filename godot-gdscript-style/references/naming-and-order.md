# Naming convention and code order

## Naming

| Item | Style | Example |
|---|---|---|
| File | snake_case | `cool_script.gd` |
| Class | PascalCase | `class_name CoolScript` |
| Node | PascalCase | `$AnimatedSprite2D` |
| Function | snake_case | `func load_level():` |
| Variable | snake_case | `var particle_effect` |
| Signal | snake_case, past tense | `signal door_opened` |
| Constant | CONSTANT_CASE | `const MAX_SPEED = 200` |
| Enum | PascalCase | `enum CoolElement` |
| Enum member | CONSTANT_CASE | `{EARTH, WATER}` |

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
