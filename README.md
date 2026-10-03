# Eat Well

A dietary restaurant finder for the Pimoroni Tufty 2350 (Badger/Badgeware).
Pick a city, filter by diet, browse the results, and open a detail view with
cuisine, price, rating, neighborhood, and notes. Each detail screen also shows
a QR code that opens the restaurant in MapQuest when scanned.

## Cities

12 US metros, 81 curated spots:

- San Francisco, CA (10)
- Twin Cities, MN (9)
- Chicago, IL (8)
- New York, NY (6)
- Los Angeles, CA (6)
- Houston, TX (6)
- Phoenix, AZ (6)
- Philadelphia, PA (6)
- San Antonio, TX (6)
- San Diego, CA (6)
- Dallas, TX (6)
- San Jose, CA (6)

## Controls

UP/DOWN moves, A selects, B or C goes back.

Flow: city picker → diet filter → results list → detail view.

Diet filters: vegan, vegetarian, gluten-free, kosher, halal — each with its
own icon.

## Near me

The first row of the city picker detects your city over the network and
jumps to its guide if one exists. The badge has no GPS, so this uses
city-level IP geolocation (no API key needed). If the network is down or
your city isn't in the guide, you get a plain message and the manual picker
keeps working.

## Disclaimer

Menus and dietary practices change. The detail screen reminds you to verify
dietary needs directly with the restaurant. Listings were researched in
October 2026 and are a curated guide, not a live ranking.

## Package and preview

Package with Python 3 (no extra packages needed):

```sh
python3 scripts/package.py eat_well
```

This creates `dist/eat_well.zip`. Open that ZIP in
[Make](https://badge.select/make) via **Open file**, then choose **Run** for
a browser preview. Or copy the `eat_well` folder to the badge's `apps`
folder over USB (double-press RESET to mount the drive).

## Data

`eat_well/data/restaurants.json` holds the listings. To add a city, follow
the same JSON shape: `id`, `name`, `aliases` (for Near-me matching), and a
`restaurants` array with `name`, `cuisine`, `price`, `diets`, `area`,
`note`, and `rating` (null when unknown).

The app entry point is `eat_well/__init__.py`; `eat_well/icons.py` draws the
diet icons.
