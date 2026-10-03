"""Diet badge icons for Eat Well.

Each diet gets a colored disc with a small white glyph, drawn with the
documented Badgeware primitives only (circle, line, text). Keep glyphs
ASCII: the badge bitmap font has no emoji or star characters.
"""

from badgeware import *

DIETS = [
    {"key": "all", "label": "All diets"},
    {"key": "vegan", "label": "Vegan", "color": (46, 139, 70), "glyph": "leaf"},
    {"key": "vegetarian", "label": "Vegetarian", "color": (124, 179, 66), "glyph": "V"},
    {"key": "gluten-free", "label": "Gluten-free", "color": (230, 126, 34), "glyph": "GF"},
    {"key": "kosher", "label": "Kosher", "color": (41, 98, 168), "glyph": "K"},
    {"key": "halal", "label": "Halal", "color": (22, 138, 130), "glyph": "moon"},
]


def diet_by_key(key):
    for diet in DIETS:
        if diet["key"] == key:
            return diet
    return DIETS[0]


def draw_diet_icon(diet, x, y, r=8):
    """Draw a diet badge disc centered at (x, y)."""
    key = diet["key"]
    if key == "all":
        screen.pen = color.rgb(110, 118, 126)
        screen.circle(x, y, r)
        screen.pen = color.white
        screen.text("*", x - 3, y - 4)
        return
    cr, cg, cb = diet["color"]
    screen.pen = color.rgb(cr, cg, cb)
    screen.circle(x, y, r)
    glyph = diet["glyph"]
    if glyph == "leaf":
        # sprout: leaf circle plus stem
        screen.pen = color.white
        screen.circle(x - 2, y - 2, 3)
        screen.line(x - 2, y + 1, x + 4, y + 5)
    elif glyph == "moon":
        # crescent: white disc with the disc color carved out
        screen.pen = color.white
        screen.circle(x, y, 4)
        screen.pen = color.rgb(cr, cg, cb)
        screen.circle(x + 2, y - 1, 4)
    else:
        # letter glyphs, roughly centered (6px per char, 8px tall)
        screen.pen = color.white
        screen.text(glyph, x - (len(glyph) * 6) // 2, y - 4)
