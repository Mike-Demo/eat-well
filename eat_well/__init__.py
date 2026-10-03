"""Eat Well: find restaurants by dietary need.

City picker (with "Near me" IP-based city detection) -> diet filter
(with icons) -> results list -> detail view.
Data lives in data/restaurants.json as a curated starter set; menus and
dietary practices change, so the detail screen reminds users to verify
directly with the restaurant.

Controls: UP/DOWN move, A selects, B or C goes back.
"""

from badgeware import *
import json

from icons import DIETS, diet_by_key
from qr_data import QR
from sprites import draw_icon, draw_splash

SPLASH_MS = 2600       # splash shows ~2.6s, any button skips
SPLASH_FRAME_MS = 450  # animation speed

badge.mode(HIRES | VSYNC)
display.backlight(0.85)

BG = color.rgb(16, 22, 26)
PANEL = color.rgb(30, 38, 45)
SELECT = color.rgb(38, 52, 60)
ACCENT = color.rgb(62, 207, 142)
WHITE = color.white
DIM = color.rgb(150, 160, 170)

W = 320
H = 240
HEADER_H = 30
FOOTER_H = 24
LIST_Y = HEADER_H + 8
ROWS = 5
ROW_H = 36

with open("data/restaurants.json") as data_file:
    APP = json.load(data_file)
CITIES = APP["cities"]

# --- state (kept outside update() so it survives between frames) ---
screen_id = "splash"  # splash | city | diet | list | detail | notice | credits
splash_start = badge.ticks
city_idx = 0
city_row = 0         # 0 = "Near me", 1..n = CITIES[city_row - 1], n+1 = Credits
city_top = 0         # scroll offset for the city picker
diet_idx = 0
list_idx = 0
list_top = 0
results = []
notice_lines = []
credits_top = 0      # scroll offset for the credits screen


CREDITS_LINES = [
    "[EAT WELL]",
    "MIT License (c) 2026",
    "Mike Demopoulos",
    "[Made with]",
    "Pixel art: Adobe Firefly",
    "Map links: MapQuest",
    "QR codes: Segno",
    "Location: ipwho.is",
    "Badge: Tufty 2350 / Badgeware",
    "[Find me]",
    "github.com/Mike-Demo",
    "x.com/Mike_Demo",
    "instagram.com/mdemop",
    "threads.com/@mdemop",
    "mikedemo.bsky.social",
    "facebook.com/mikedemo42",
    "mike-demo.tumblr.com",
    "linkedin.com/in/mikedemopoulos",
    "mikedemo.com",
]
CREDITS_ROWS = 12


def current_diet():
    return DIETS[diet_idx]


def apply_filter():
    global results, list_idx, list_top
    key = current_diet()["key"]
    spots = CITIES[city_idx]["restaurants"]
    if key == "all":
        results = spots
    else:
        results = [r for r in spots if key in r["diets"]]
    list_idx = 0
    list_top = 0


def wrap(text, width):
    words = text.split(" ")
    lines = []
    line = ""
    for word in words:
        while len(word) > width:  # hard-break words longer than the width
            if line:
                lines.append(line)
                line = ""
            lines.append(word[:width])
            word = word[width:]
        piece = word if not line else line + " " + word
        if len(piece) <= width:
            line = piece
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def header(title):
    screen.pen = PANEL
    screen.rectangle(0, 0, W, HEADER_H)
    screen.pen = ACCENT
    screen.text("EAT WELL", 10, 9)
    screen.pen = DIM
    screen.text(title, 112, 9)


def footer(hint):
    screen.pen = PANEL
    screen.rectangle(0, H - FOOTER_H, W, FOOTER_H)
    screen.pen = DIM
    screen.text(hint, 10, H - FOOTER_H + 8)


def locate_city():
    """Detect the user's city over the network and match it to the guide.

    Returns (True, city_index) on a match, or (False, message) otherwise.
    The badge runtime has no GPS, so this uses IP-based geolocation
    (city-level accuracy). Any network failure degrades to a message;
    bundled data always remains available.
    """
    try:
        import requests
    except ImportError:
        return (False, "Location needs the badge runtime.")
    try:
        resp = requests.get("https://ipwho.is/", timeout=3)
        data = resp.json()
        resp.close()
    except (OSError, ValueError):
        return (False, "Location unavailable. Check connection.")
    if not data.get("success"):
        return (False, "Location lookup failed.")
    detected = str(data.get("city") or "").strip().lower()
    for i, city in enumerate(CITIES):
        names = [city["name"].lower()]
        names += [a.lower() for a in city.get("aliases", [])]
        for name in names:
            if detected and (detected in name or name in detected):
                return (True, i)
    label = str(data.get("city") or "Unknown")
    return (False, "Near: " + label + ". Not in the guide yet.")


def show_notice(message):
    global screen_id, notice_lines
    notice_lines = wrap(message, 37)
    screen_id = "notice"


CITY_ROWS = 6
CITY_ROW_H = 28


def draw_city():
    header("Choose a city")
    y = LIST_Y
    # row 0: Near me
    if city_top == 0:
        if city_row == 0:
            screen.pen = SELECT
            screen.rectangle(6, y - 4, W - 12, 24)
            screen.pen = ACCENT
            screen.text(">", 12, y)
        screen.pen = color.rgb(62, 207, 142)
        screen.circle(24, y + 4, 6)
        screen.circle(24, y + 4, 2)
        screen.pen = WHITE if city_row == 0 else DIM
        screen.text("Near me", 40, y)
        screen.pen = DIM
        screen.text("detect my city", 210, y)
        y += CITY_ROW_H
    for i in range(max(0, city_top - 1), min(len(CITIES), city_top + CITY_ROWS - 1)):
        row = i + 1
        if row == city_row:
            screen.pen = SELECT
            screen.rectangle(6, y - 4, W - 12, 24)
            screen.pen = ACCENT
            screen.text(">", 12, y)
        city = CITIES[i]
        draw_icon("city-" + city["id"], 26, y - 4)
        screen.pen = WHITE if row == city_row else DIM
        screen.text(city["name"], 56, y)
        screen.pen = DIM
        screen.text(str(len(city["restaurants"])) + " spots", 218, y)
        y += CITY_ROW_H
    credits_row = len(CITIES) + 1
    if city_top <= credits_row < city_top + CITY_ROWS:
        if credits_row == city_row:
            screen.pen = SELECT
            screen.rectangle(6, y - 4, W - 12, 24)
            screen.pen = ACCENT
            screen.text(">", 12, y)
        screen.pen = WHITE if credits_row == city_row else DIM
        screen.text("Credits", 56, y)
        screen.pen = DIM
        screen.text("license & sources", 200, y)
        y += CITY_ROW_H
    rows = len(CITIES) + 2  # Near me + cities + Credits
    if rows > CITY_ROWS:
        screen.pen = DIM
        screen.text(str(city_top + 1) + "-" + str(min(city_top + CITY_ROWS, rows)) +
                    " of " + str(rows), 12, H - FOOTER_H - 14)
    footer("UP/DN move   A select")


def draw_credits():
    header("Credits")
    y = LIST_Y
    style = DIM
    shown = 0
    for line in CREDITS_LINES[credits_top:]:
        if shown >= CREDITS_ROWS:
            break
        if line.startswith("["):
            screen.pen = ACCENT
            screen.text(line[1:-1], 12, y)
            style = WHITE if "Find me" in line else DIM
        else:
            screen.pen = style
            screen.text(line, 12, y)
        y += 14
        shown += 1
    if len(CREDITS_LINES) > CREDITS_ROWS:
        screen.pen = DIM
        screen.text(str(credits_top + 1) + "-" +
                    str(min(credits_top + CREDITS_ROWS, len(CREDITS_LINES))) +
                    " of " + str(len(CREDITS_LINES)), 12, H - FOOTER_H - 14)
    footer("UP/DN scroll   B back")


def draw_notice():
    header("Near me")
    y = 90
    screen.pen = DIM
    for line in notice_lines:
        screen.text(line, 20, y)
        y += 15
    footer("B back")


def draw_diet():
    header("Filter by diet")
    y = LIST_Y
    for i, diet in enumerate(DIETS):
        if i == diet_idx:
            screen.pen = SELECT
            screen.rectangle(6, y - 6, W - 12, 26)
        draw_icon("diet-" + diet["key"], 16, y - 4)
        screen.pen = WHITE if i == diet_idx else DIM
        screen.text(diet["label"], 48, y)
        y += 30
    footer("UP/DN move   A select   B back")


def draw_list():
    header(CITIES[city_idx]["name"] + " / " + current_diet()["label"])
    if not results:
        screen.pen = DIM
        screen.text("No matches for this filter.", 20, 90)
        screen.text("Press B and try another diet.", 20, 106)
    else:
        y = LIST_Y
        for i in range(list_top, min(list_top + ROWS, len(results))):
            spot = results[i]
            if i == list_idx:
                screen.pen = SELECT
                screen.rectangle(6, y - 4, W - 12, ROW_H)
            screen.pen = WHITE if i == list_idx else DIM
            name = spot["name"]
            if len(name) > 28:
                name = name[:27] + "..."
            screen.text(name, 12, y)
            screen.pen = DIM
            screen.text(spot["cuisine"] + "  " + spot["price"], 12, y + 14)
            rating = spot["rating"]
            screen.text("RT " + (str(rating) if rating else "-"), 200, y + 14)
            ix = 308
            for key in spot["diets"]:
                draw_icon("diet-" + key, ix - 12, y + 6, small=True)
                ix -= 16
            y += ROW_H
        if len(results) > ROWS:
            screen.pen = DIM
            screen.text(str(list_top + 1) + "-" + str(min(list_top + ROWS, len(results))) +
                        " of " + str(len(results)), 12, H - FOOTER_H - 14)
    footer("UP/DN scroll   A details   B back")


def draw_detail():
    spot = results[list_idx]
    qr_key = CITIES[city_idx]["id"] + "|" + spot["name"]
    geom = qr_geom(qr_key)
    qr_x = geom[0] if geom else W  # keep text clear of the QR's left edge
    header("Details")
    y = LIST_Y
    screen.pen = WHITE
    for line in wrap(spot["name"], 36):
        screen.text(line, 12, y)
        y += 14
    screen.pen = DIM
    rating = spot["rating"]
    screen.text(spot["cuisine"] + "  " + spot["price"] + "  RT " +
                (str(rating) if rating else "-"), 12, y)
    y += 16
    screen.text(spot["area"], 12, y)
    y += 20
    screen.pen = ACCENT
    screen.text("Good for:", 12, y)
    y += 16
    for key in spot["diets"]:
        diet = diet_by_key(key)
        draw_icon("diet-" + key, 14, y - 1, small=True)
        screen.pen = WHITE
        screen.text(diet["label"], 34, y)
        y += 20
    y += 4
    # Note: wrap narrow enough to clear the QR, and stop above the disclaimer.
    note_width = (qr_x - 12 - 8) // 8 if geom else 34
    max_lines = max(0, (DISCLAIMER_Y - 6 - y) // 13)
    note_lines = wrap(spot["note"], note_width)
    shown = note_lines[:max_lines]
    if len(note_lines) > max_lines and shown:
        shown[-1] = shown[-1][:max(0, note_width - 3)] + "..."
    screen.pen = DIM
    for line in shown:
        screen.text(line, 12, y)
        y += 13
    draw_qr(qr_key)
    screen.pen = color.rgb(190, 150, 60)
    screen.text("Menus change, verify directly", 12, DISCLAIMER_Y)
    footer("B back   Scan QR for map")


QR_SCALE = 2
QR_QUIET = 2  # quiet-zone modules on each side
DISCLAIMER_Y = H - FOOTER_H - 14  # gold reminder line above the footer
_qr_cache = {}


def qr_matrix(key):
    """Decode a packed QR entry once and cache it. Returns (size, bytes)."""
    hit = _qr_cache.get(key)
    if hit is None:
        size, hexdata = QR[key]
        raw = bytearray(len(hexdata) // 2)
        for i in range(0, len(hexdata), 2):
            raw[i // 2] = int(hexdata[i:i + 2], 16)
        hit = (size, raw)
        _qr_cache[key] = hit
    return hit


def qr_geom(key):
    """Return (x0, y0, total) for a QR code, or None when the key has none."""
    if key not in QR:
        return None
    size, _raw = qr_matrix(key)
    total = (size + QR_QUIET * 2) * QR_SCALE
    return (W - total - 8, H - FOOTER_H - total - 6, total)


def draw_qr(key):
    """Draw the MapQuest QR code for a restaurant, bottom-right above footer."""
    geom = qr_geom(key)
    if geom is None:
        return
    x0, y0, total = geom
    size, raw = qr_matrix(key)
    screen.pen = WHITE
    screen.rectangle(x0, y0, total, total)
    screen.pen = color.black
    bit = 0
    for row in range(size):
        for col in range(size):
            if (raw[bit // 8] >> (7 - bit % 8)) & 1:
                screen.rectangle(x0 + (col + QR_QUIET) * QR_SCALE,
                                 y0 + (row + QR_QUIET) * QR_SCALE,
                                 QR_SCALE, QR_SCALE)
            bit += 1


def draw_splash_screen():
    frame = (badge.ticks // SPLASH_FRAME_MS) % 4
    draw_splash(frame)


def _splash_elapsed():
    dt = badge.ticks - splash_start
    return dt if dt >= 0 else SPLASH_MS + 1  # tick counter wrapped: just advance


def update():
    global screen_id, city_idx, city_row, city_top, diet_idx, list_idx, list_top
    global credits_top

    if screen_id == "splash":
        if badge.pressed() or _splash_elapsed() > SPLASH_MS:
            screen_id = "city"
    elif screen_id == "city":
        rows = len(CITIES) + 2
        if badge.pressed(BUTTON_UP):
            city_row = (city_row - 1) % rows
        elif badge.pressed(BUTTON_DOWN):
            city_row = (city_row + 1) % rows
        # keep the selected row visible after either direction, incl. wrap
        if city_row < city_top:
            city_top = city_row
        elif city_row >= city_top + CITY_ROWS:
            city_top = city_row - CITY_ROWS + 1
        if badge.pressed(BUTTON_A):
            if city_row == 0:
                ok, value = locate_city()
                if ok:
                    city_idx = value
                    diet_idx = 0
                    screen_id = "diet"
                else:
                    show_notice(value)
            elif city_row == len(CITIES) + 1:
                credits_top = 0
                screen_id = "credits"
            else:
                city_idx = city_row - 1
                diet_idx = 0
                screen_id = "diet"
    elif screen_id == "diet":
        if badge.pressed(BUTTON_UP):
            diet_idx = (diet_idx - 1) % len(DIETS)
        elif badge.pressed(BUTTON_DOWN):
            diet_idx = (diet_idx + 1) % len(DIETS)
        elif badge.pressed(BUTTON_A):
            apply_filter()
            screen_id = "list"
        elif badge.pressed(BUTTON_B) or badge.pressed(BUTTON_C):
            screen_id = "city"
    elif screen_id == "list":
        if results:
            if badge.pressed(BUTTON_UP):
                list_idx = (list_idx - 1) % len(results)
                if list_idx < list_top:
                    list_top = list_idx
            elif badge.pressed(BUTTON_DOWN):
                list_idx = (list_idx + 1) % len(results)
                if list_idx >= list_top + ROWS:
                    list_top = list_idx - ROWS + 1
            elif badge.pressed(BUTTON_A):
                screen_id = "detail"
        if badge.pressed(BUTTON_B) or badge.pressed(BUTTON_C):
            screen_id = "diet"
    elif screen_id == "detail":
        if badge.pressed(BUTTON_A) or badge.pressed(BUTTON_B) or badge.pressed(BUTTON_C):
            screen_id = "list"
    elif screen_id == "notice":
        if badge.pressed(BUTTON_A) or badge.pressed(BUTTON_B) or badge.pressed(BUTTON_C):
            screen_id = "city"
    elif screen_id == "credits":
        max_top = max(0, len(CREDITS_LINES) - CREDITS_ROWS)
        if badge.pressed(BUTTON_UP):
            credits_top = max(0, credits_top - 1)
        elif badge.pressed(BUTTON_DOWN):
            credits_top = min(max_top, credits_top + 1)
        if badge.pressed(BUTTON_B) or badge.pressed(BUTTON_C):
            screen_id = "city"

    screen.pen = BG
    screen.clear()
    if screen_id == "splash":
        draw_splash_screen()
    elif screen_id == "city":
        draw_city()
    elif screen_id == "diet":
        draw_diet()
    elif screen_id == "list":
        draw_list()
    elif screen_id == "detail":
        draw_detail()
    elif screen_id == "notice":
        draw_notice()
    elif screen_id == "credits":
        draw_credits()


print("Eat Well: UP/DN move, A select, B back.")
run(update)
