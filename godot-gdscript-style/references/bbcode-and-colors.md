# BBCode in RichTextLabel

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
| Tooltip | `[hint=text]` |
| Link (emits `meta_clicked`) | `[url=]` |

More tags exist: `img`, `table`, `cell`, `dropcap`, `char`, `lang`.

## Animated effects

| Effect | Defaults |
|---|---|
| `[rainbow]` | `freq=1.0 sat=0.6 val=0.8 speed=0.1` |
| `[fade]` | `start=4 length=14` |
| `[pulse]` | `freq=1.0 color=red ease=-2.0` |
| `[shake]` | `rate=9.0 level=5 connected=1` |
| `[wave]` | `freq=1.0 amp=5.0 connected=1` |
| `[tornado]` | `freq=1.0 radius=5.0 connected=1` |

## Image tag

```
[img]res://image.png[/img]
[img=top,top,40x60]res://image.png[/img]
[img align=t,t width=40 height=60]res://image.png[/img]
```

Options: `width`, `height`, `color` (tint), `align`, `region` (x,y,w,h), `pad` (bool), `tooltip`, `alt` (accessibility text).

# Named colors

- Use `Color.NAME` in GDScript. Example: `Color.CORAL`.
- Use `[color=name]` in BBCode. Example: `[color=coral]`.
- Colors under 8 characters: `coral`, `tomato`, `dark_red`, `salmon`, `brown`, `khaki`, `moccasin`, `tan`, `peru`, `sienna`, `olive`, `sky_blue`, `teal`, `orchid`, `violet`, `plum`, `thistle`, `purple`, `indigo`, `snow`, `seashell`, `linen`, `old_lace`, `ivory`, `honeydew`, `azure`, `lavender`, `bisque`, `wheat`, `cornsilk`, `beige`, `black`, `dim_gray`, `web_gray`, `gray`, `silver`, `white`, `red`, `orange`, `gold`, `yellow`, `green`, `cyan`, `blue`, `magenta`.
- The full list matches the CSS and X11 color names.
- Godot variants use the `web_` prefix to separate the CSS value from the X11 value: `web_maroon`, `web_gray`, `web_green`, `web_purple`.
- Contrast: check text and background contrast against WCAG AA (4.5:1) before choosing a named color.
