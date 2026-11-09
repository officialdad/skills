# BBCode in RichTextLabel

Source: [BBCode in RichTextLabel, Godot 4.7](https://docs.godotengine.org/en/4.7/tutorials/ui/bbcode_in_richtextlabel.html) and `scene/gui/rich_text_label.cpp` at `4.7.2-stable`.

Scope: project-d20 has no `RichTextLabel`, no `bbcode_enabled`, and no BBCode string today. The HUD is drawn art. This file is a reference for the first use. Doc comment BBCode is a different set: see `doc-comments.md`.

Set `bbcode_enabled = true` on the node.

## Tags

| Purpose | Tag |
|---|---|
| Bold, italic | `[b]` `[i]` |
| Underline, strike (optional color) | `[u color=]` `[s color=]` |
| Mono font | `[code]` |
| Font, size | `[font=]` `[font_size=]` |
| Text color | `[color=]` |
| Background, foreground color | `[bgcolor=]` `[fgcolor=]` |
| Outline | `[outline_color=]` `[outline_size=]` |
| Horizontal rule | `[hr]` |
| Line break | `[br]` |
| Literal brackets | `[lb]` `[rb]` |
| Ordered list | `[ol type=]` |
| Unordered list | `[ul bullet=]` |
| Indent | `[indent]` |
| Paragraph | `[p align=]` |
| Alignment | `[center]` `[left]` `[right]` `[fill]` |
| Tooltip | `[hint="text"]`. Quote the text. |
| Link (emits `meta_clicked`) | `[url=]` |

More tags exist: `img`, `table`, `cell`, `dropcap`, `char`, `lang`.

## Animated effects

Defaults come from the engine source. The docs show other values for `[fade]` (`start=4 length=14`) and `[wave]` (`amp=50.0`). The engine wins.

| Effect | Defaults |
|---|---|
| `[rainbow]` | `freq=1.0 sat=0.8 val=0.8 speed=1.0` |
| `[fade]` | `start=0 length=10` |
| `[pulse]` | `freq=1.0 color=#ffffff40 ease=-2.0` |
| `[shake]` | `rate=20.0 level=5 connected=1` |
| `[wave]` | `freq=5.0 amp=20.0 connected=1` |
| `[tornado]` | `freq=1.0 radius=10.0 connected=1` |

## Image tag

```
[img]res://image.png[/img]
[img=40x60]res://image.png[/img]
[img=top,top]res://image.png[/img]
[img align=t,t width=40 height=60]res://image.png[/img]
```

- Write size and alignment through the options form. The `[img=...]` form takes a size or an alignment, never both.
- Options: `width`, `height`, `color` (tint), `align`, `region` (x,y,w,h), `pad` (bool), `tooltip`, `alt` (accessibility text).
- `width` and `height` take a float and an `em` unit in 4.7.

## Named colors

The project writes colors as hex or reads them from `data/*.json`. Never rewrite an existing hex color as a named color.

- Use `Color.NAME` in GDScript. Example: `Color.CORAL`.
- Use `[color=name]` in BBCode. Example: `[color=coral]`.
- Short color names, 8 characters or fewer. This is a sample, not the full list: `coral`, `tomato`, `dark_red`, `salmon`, `brown`, `khaki`, `moccasin`, `tan`, `peru`, `sienna`, `olive`, `sky_blue`, `teal`, `orchid`, `violet`, `plum`, `thistle`, `purple`, `indigo`, `snow`, `seashell`, `linen`, `old_lace`, `ivory`, `honeydew`, `azure`, `lavender`, `bisque`, `wheat`, `cornsilk`, `beige`, `black`, `dim_gray`, `web_gray`, `gray`, `silver`, `white`, `red`, `orange`, `gold`, `yellow`, `green`, `cyan`, `blue`, `magenta`.
- The full list is the X11 color names plus `transparent`. The `Color` class has 146 constants.
- The `web_` constants hold the CSS value where it differs from the X11 value: `web_maroon`, `web_gray`, `web_green`, `web_purple`.
- Contrast: check text and background contrast against WCAG AA (4.5:1) before choosing a named color.
