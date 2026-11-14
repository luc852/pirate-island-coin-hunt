"""Buried treasure: where the chest hides and how the bottle's message says so.

Every island buries one chest under an ordinary sand tile and washes up one
message in a bottle. The message is a riddle whose difficulty climbs with the
islands: plain paces, paces from a landmark, mirror writing, a letter-shift
cipher, and finally a row-and-column crossing. Positions are re-rolled every
voyage, so a riddle can be solved but never memorised.

The secret island swaps the chest for four rune plates that have to be trodden
in the order a verse describes.
"""
import random

NUMBER_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven",
                "eight", "nine", "ten", "eleven", "twelve", "thirteen",
                "fourteen", "fifteen", "sixteen", "seventeen", "eighteen",
                "nineteen", "twenty"]

LANDMARKS = {
    "anchor": "the rusty anchor",
    "skull": "the bleached skull",
    "starfish": "the red starfish",
    "wheel": "the broken ship's wheel",
}

RUNES = ["sun", "moon", "star", "skull"]
RUNE_VERSES = {
    "sun": "the eye that burns away the morning mist",
    "moon": "the silver coin no pirate ever spent",
    "star": "the spark that steers a ship when charts are lost",
    "skull": "the grin that guards what dead men never lent",
}


def open_tiles(grid):
    return [(c, r) for r, row in enumerate(grid) for c, ch in enumerate(row)
            if ch == '.']


def _dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def paces(dx, dy):
    """'three paces east and two paces north' for a tile offset."""
    parts = []
    if dx:
        n = abs(dx)
        parts.append(f"{NUMBER_WORDS[n]} pace{'s' if n > 1 else ''} "
                     f"{'east' if dx > 0 else 'west'}")
    if dy:
        n = abs(dy)
        parts.append(f"{NUMBER_WORDS[n]} pace{'s' if n > 1 else ''} "
                     f"{'south' if dy > 0 else 'north'}")
    return " and ".join(parts)


def caesar(text, shift=1):
    out = []
    for ch in text:
        if ch.isalpha():
            out.append(chr((ord(ch.upper()) - 65 + shift) % 26 + 65))
        else:
            out.append(ch)
    return "".join(out)


def plan(grid, kind, start, rng=None):
    """Lay out one island's secret.

    Returns {"chest", "bottle", "landmarks": [(kind, tile)], "title",
    "lines": [(style, text)]} where style is "body", "cipher" or "hint".
    """
    rng = rng or random.Random()
    tiles = open_tiles(grid)
    far = [t for t in tiles if _dist(t, start) >= 5]

    chest = marks = None
    for _ in range(200):
        chest = rng.choice(far)
        marks = _place_landmarks(tiles, chest, kind, rng)
        if marks:
            break
    names = list(marks)
    a = marks[names[0]]
    dx, dy = chest[0] - a[0], chest[1] - a[1]

    gull = "Count the paces as the gull flies - crates or no crates."
    if kind == "paces":
        lines = [("body", "From the very spot where ye waded ashore, walk "
                          f"{paces(chest[0] - start[0], chest[1] - start[1])}."),
                 ("body", "Dig there, and dig true."),
                 ("hint", gull)]
    elif kind == "landmark":
        lines = [("body", f"Seek {LANDMARKS[names[0]]}. From it, walk {paces(dx, dy)}."),
                 ("body", "There sleeps the chest."),
                 ("hint", gull)]
    elif kind == "mirror":
        plain = f"FROM {LANDMARKS[names[0]]} WALK {paces(dx, dy)}".upper()
        lines = [("body", "Seawater got in, and the ink has run backwards:"),
                 ("cipher", plain[::-1]),
                 ("hint", "Read it from the far end. " + gull)]
    elif kind == "caesar":
        plain = f"FROM {LANDMARKS[names[0]]} WALK {paces(dx, dy)}".upper()
        lines = [("body", "A careful hand wrote this. Every letter has slipped "
                          "one berth down the alphabet, so A became B:"),
                 ("cipher", caesar(plain, 1)),
                 ("hint", "Slide each letter back by one. " + gull)]
    else:  # crossing
        lines = [("body", f"The chest lies in the same ROW as {LANDMARKS[names[0]]}"
                          f" and the same COLUMN as {LANDMARKS[names[1]]}."),
                 ("body", "Where the two lines cross, dig."),
                 ("hint", "Rows run east to west; columns run north to south.")]

    taken = {chest, start} | set(marks.values())
    spots = [t for t in tiles if t not in taken and _dist(t, start) >= 4
             and _dist(t, chest) >= 4] or [t for t in tiles if t not in taken]
    bottle = rng.choice(spots)

    return {"chest": chest, "bottle": bottle,
            "landmarks": list(marks.items()),
            "title": "A Message in a Bottle", "lines": lines}


def _place_landmarks(tiles, chest, kind, rng):
    """Three landmarks. The first one or two carry the clue; the rest are
    red herrings, so the riddle has to be read rather than guessed."""
    kinds = list(LANDMARKS)
    rng.shuffle(kinds)
    marks = {}
    if kind == "crossing":
        row = [t for t in tiles if t[1] == chest[1] and abs(t[0] - chest[0]) >= 2]
        col = [t for t in tiles if t[0] == chest[0] and abs(t[1] - chest[1]) >= 2]
        if not row or not col:
            return None
        marks[kinds[0]] = rng.choice(row)
        marks[kinds[1]] = rng.choice(col)
    else:
        near = [t for t in tiles if 2 <= _dist(t, chest) <= 6
                and abs(t[0] - chest[0]) <= 5 and abs(t[1] - chest[1]) <= 4]
        if not near:
            return None
        marks[kinds[0]] = rng.choice(near)
    for k in kinds:
        if len(marks) >= 3:
            break
        if k in marks:
            continue
        free = [t for t in tiles if t != chest
                and all(_dist(t, m) >= 3 for m in marks.values())
                # A decoy sharing the chest's row or column would muddy a crossing clue.
                and t[0] != chest[0] and t[1] != chest[1]]
        if free:
            marks[k] = rng.choice(free)
    return marks


def warmth(tile, chest):
    """What the shovel tells you about a wrong hole."""
    d = max(abs(tile[0] - chest[0]), abs(tile[1] - chest[1]))
    if d <= 1:
        return "Burning hot! The chest is a single pace away."
    if d <= 3:
        return "Warm... the sand here has been turned before."
    return "Cold sand. Nothing but crabs' leavings."


def rune_plan(rng=None):
    """The order the four plates must be trodden, and the verse that says so."""
    rng = rng or random.Random()
    order = RUNES[:]
    rng.shuffle(order)
    lead = ["First tread upon", "then", "then", "and last,"]
    lines = [("body", "Four stones wake the vault, but only in their turn:")]
    for word, rune in zip(lead, order):
        lines.append(("cipher", f"{word} {RUNE_VERSES[rune]}"))
    lines.append(("hint", "Each verse names one of the carved plates. "
                          "A wrong step and the cove starts over - and stirs."))
    return {"order": order, "title": "Carved Above the Vault", "lines": lines}
