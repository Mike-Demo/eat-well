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

from icons import DIETS, draw_diet_icon, diet_by_key

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
screen_id = "city"   # city | diet | list | detail | notice
city_idx = 0
city_row = 0         # 0 = "Near me", 1..n = CITIES[city_row - 1]
city_top = 0         # scroll offset for the city picker
diet_idx = 0
list_idx = 0
list_top = 0
results = []
notice_lines = []


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
    notice_lines = wrap(message, 38)
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
        screen.pen = WHITE if row == city_row else DIM
        screen.text(city["name"], 40, y)
        screen.pen = DIM
        screen.text(str(len(city["restaurants"])) + " spots", 210, y)
        y += CITY_ROW_H
    rows = len(CITIES) + 1
    if rows > CITY_ROWS:
        screen.pen = DIM
        screen.text(str(city_top + 1) + "-" + str(min(city_top + CITY_ROWS, rows)) +
                    " of " + str(rows), 12, H - FOOTER_H - 14)
    footer("UP/DN move   A select")


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
        draw_diet_icon(diet, 24, y + 4, 8)
        screen.pen = WHITE if i == diet_idx else DIM
        screen.text(diet["label"], 44, y)
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
            ix = 296
            for key in spot["diets"]:
                draw_diet_icon(diet_by_key(key), ix, y + 8, 8)
                ix -= 20
            y += ROW_H
        if len(results) > ROWS:
            screen.pen = DIM
            screen.text(str(list_top + 1) + "-" + str(min(list_top + ROWS, len(results))) +
                        " of " + str(len(results)), 12, H - FOOTER_H - 14)
    footer("UP/DN scroll   A details   B back")


def draw_detail():
    spot = results[list_idx]
    header("Details")
    y = LIST_Y
    screen.pen = WHITE
    for line in wrap(spot["name"], 40):
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
        draw_diet_icon(diet, 20, y + 4, 8)
        screen.pen = WHITE
        screen.text(diet["label"], 36, y)
        y += 20
    y += 4
    screen.pen = DIM
    for line in wrap(spot["note"], 44):
        screen.text(line, 12, y)
        y += 13
    screen.pen = color.rgb(190, 150, 60)
    screen.text("Menus change. Verify dietary needs directly.", 12, H - FOOTER_H - 14)
    footer("B back")


def update():
    global screen_id, city_idx, city_row, city_top, diet_idx, list_idx, list_top

    if screen_id == "city":
        rows = len(CITIES) + 1
        if badge.pressed(BUTTON_UP):
            city_row = (city_row - 1) % rows
            if city_row < city_top:
                city_top = city_row
        elif badge.pressed(BUTTON_DOWN):
            city_row = (city_row + 1) % rows
            if city_row >= city_top + CITY_ROWS:
                city_top = city_row - CITY_ROWS + 1
        elif badge.pressed(BUTTON_A):
            if city_row == 0:
                ok, value = locate_city()
                if ok:
                    city_idx = value
                    diet_idx = 0
                    screen_id = "diet"
                else:
                    show_notice(value)
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

    screen.pen = BG
    screen.clear()
    if screen_id == "city":
        draw_city()
    elif screen_id == "diet":
        draw_diet()
    elif screen_id == "list":
        draw_list()
    elif screen_id == "detail":
        draw_detail()
    elif screen_id == "notice":
        draw_notice()


print("Eat Well: UP/DN move, A select, B back.")
run(update)
