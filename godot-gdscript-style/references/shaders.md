# Shaders

## Uniforms

Syntax: `uniform type name : hints = default;`

| Need | Declaration |
|---|---|
| Bool | `uniform bool a_bool = true;` |
| Int | `uniform int a_int = -100;` |
| Float | `uniform float a_float = 1.00;` |
| Float range | `uniform float x : hint_range(min, max, STEP);` |
| Int dropdown | `uniform int size : hint_enum("Tiny:2", "Big:9");` |
| Vector | `uniform vec2 dir = vec2(1.0, 0.0);` |
| Color RGB | `uniform vec3 my_color : source_color;` |
| Color RGBA | `uniform vec4 my_color : source_color;` |
| Texture | `uniform sampler2D my_tex;` |
| sRGB texture | `uniform sampler2D my_tex : source_color;` |
| Optional texture | `uniform sampler2D my_tex : hint_default_white;` |
| Screen texture | `uniform sampler2D screen : hint_screen_texture;` |
| Array | `uniform type my_param[size];` |
| Per node | `instance uniform` (16 max) |
| Per project | `global uniform` |
| Group | `group_uniforms group_name;` and `group_uniforms name.subname;` |
| End group | `group_uniforms;` |
| Precision | `lowp` `mediump` `highp` |
| Doc comment | `/** text */` above the uniform |

- Read the Godot docs before using `instance uniform`, `global uniform`, or precision qualifiers.
- Toggle comments with Ctrl+K in the shader editor.
- Types: `mat2/3/4`, `ivec2/3/4`, `uvec2/3/4`, `bvec2/3/4`, `isampler2D/3D/2DArray`, `usampler2D/3D/2DArray`, `samplerCube`, `samplerCubeArray`.

## Sampler hints

Syntax: `uniform sampler2D my_texture : source_color, repeat_enable;`

| Need | Hint |
|---|---|
| White if empty | `hint_default_white` |
| Black if empty | `hint_default_black` |
| Transparent if empty | `hint_default_transparent` |
| Smooth filtering (default) | `filter_linear` |
| Pixelated filtering | `filter_nearest` |
| Mipmaps | `filter_linear_mipmap`, `filter_nearest_mipmap` |
| Anisotropic mipmaps | `filter_linear_mipmap_anisotropic`, `filter_nearest_mipmap_anisotropic` |
| Repeat | `repeat_enable` |
| Clamp | `repeat_disable` |
| sRGB color | `source_color` |
| Normal map | `hint_normal` |
| Roughness | `hint_roughness_{r,g,b,a,normal,gray}` |
| Flowmap | `hint_anisotropy` |
| Normal and roughness | `hint_normal_roughness_texture` (Forward+ only) |
| Screen texture | `hint_screen_texture` |
| Depth texture | `hint_depth_texture` (spatial shader only) |

Pixel art: use `filter_nearest` on every sprite texture.

## Set shader parameters from GDScript

```gdscript
material.set_shader_parameter("name", value)
tween_property(material, "shader_parameter/name", ...)
set_instance_shader_parameter("x", value)
tween_property(self, "instance_shader_parameters/x", ...)
RenderingServer.global_shader_parameter_set(...)
```
