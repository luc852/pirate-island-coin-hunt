"""Level layouts.

Grid legend:
  '#' wall / obstacle
  '.' open sand
  '~' puddle (hazard)
  'C' coin
  'M' monster spawn
  'P' player start
  '1'-'4' rune plate, 'V' vault door, 'K' crown (secret island only)

All levels are generated from a recursive-backtracker maze (guaranteed fully
connected) with a "braid" factor controlling how open vs. maze-like the level
feels. Later levels are less braided -> tighter, more maze-like.
"""

TILE_SIZE = 40

LEVEL_1 = [
    '#####################',
    '#P..........C.......#',
    '#.#.#.#.#.#.#.#~#.#.#',
    '#...C...#M..........#',
    '#.#.#C#.#.#.#.###.#.#',
    '#.........#....C..~C#',
    '###.#.#.#.#.#.#.###.#',
    '#..........C........#',
    '#.#C###.#.#.#~#.#.#M#',
    '#.........#.......#.#',
    '#.#.#.#.#.#.#.#.#.#.#',
    '#.........C.........#',
    '#####################',
]

LEVEL_2 = [
    '#####################',
    '#P#..C.......C..#...#',
    '#.#.#####.#C#~#.#.###',
    '#.#.........#...#...#',
    '#.#.###.###.#.#.#.#.#',
    '#.......C....~......#',
    '#.#.#.#.#.#.#.#.#~#.#',
    '#..M~C....#.#.......#',
    '#.#C#.###.#.#.#M#C#.#',
    '#.C...#..C...C....#.#',
    '#.#M#.#.#.###.###.#.#',
    '#...................#',
    '#####################',
]

LEVEL_3 = [
    '#####################',
    '#P..................#',
    '#.#.#####.#####C#.#.#',
    '#....C..#C#.C.C..C..#',
    '#.###.#.#.#.#.#.###.#',
    '#.....C...#.#...#.#.#',
    '#.###.#.###.#####.#~#',
    '#.#~...~.....C.CM..M#',
    '#.#.#.###M#.###.###M#',
    '#.#.#.........C~#...#',
    '#.#.#.###C###.#.#.#.#',
    '#..~#.....C...#.....#',
    '#####################',
]

LEVEL_4 = [
    '#####################',
    '#P#...~...C.#.......#',
    '#.###.#####.#.#####.#',
    '#...#....C....#~..#.#',
    '#.#.#C###C#.#.#.###C#',
    '#~M.#.....#M..#.....#',
    '#.#.###.#.#~###.#####',
    '#.....M.#.#.C.....CM#',
    '#.#.###.#.###~#.#.#.#',
    '#...#..CCM#.C.....#.#',
    '#C#.#.#.#.#.#######C#',
    '#.C...#.......C.....#',
    '#####################',
]

LEVEL_5 = [
    '#####################',
    '#P..C.#.C.#.......#.#',
    '#####.###.#.###.#M#.#',
    '#...#...#C..#...#.#.#',
    '#.#C###.#####.###.#.#',
    '#.#.#C..#...#M#C.C#.#',
    '#.#.#C###.#.#.#.###.#',
    '#.#...#.CM#.#.#.C..C#',
    '###.#C#.#M#.#M#####.#',
    '#....~#~#.#.#.#..M..#',
    '#.###C###.#.#.#C#####',
    '#...MC....#...#....C#',
    '#####################',
]

# The hidden sixth island. Reached only with all five map fragments.
#   '1'-'4' rune plates, 'V' vault door, 'K' the crown that ends the run.
SECRET_GRID = [
    '#####################',
    '#P...C....#........1#',
    '#.###.###.#.###.###.#',
    '#.#..M..#...#.....#.#',
    '#.#.###.##V##.###.#.#',
    '#...#C#.#CCC#.#C#...#',
    '#.#.#...#CKC#...#.#.#',
    '#..~#.#.#CCC#.#.#~..#',
    '#.#.###.#####.###.#.#',
    '#.#.....#.4.#..M..#.#',
    '#.###.###.#.###.###.#',
    '#2........#...C....3#',
    '#####################',
]

# monster_mode: 'wander' = random movement only
#               'mix'    = wanders most of the time, occasionally chases slowly
#               'chase'  = actively chases the player
# mood:   time of day, which picks the sea, the light and the lantern
# par:    seconds; finishing under it earns a time bonus
# clue:   how the bottle's message hides the chest (see treasure.py)
# events: which random events may strike this island (see events.py)
LEVELS = [
    {"grid": LEVEL_1, "monster_mode": "wander", "monster_speed": 60,
     "name": "Driftwood Landing", "mood": "dawn", "par": 60,
     "clue": "paces", "events": ["gold", "storm"]},
    {"grid": LEVEL_2, "monster_mode": "wander", "monster_speed": 70,
     "name": "Crab Claw Cay", "mood": "noon", "par": 70,
     "clue": "landmark", "events": ["storm", "gold", "kraken"]},
    {"grid": LEVEL_3, "monster_mode": "mix", "monster_speed": 75,
     "name": "Smuggler's Maze", "mood": "golden", "par": 80,
     "clue": "mirror", "events": ["kraken", "storm", "gold"]},
    {"grid": LEVEL_4, "monster_mode": "mix", "monster_speed": 85,
     "name": "Storm Reef", "mood": "dusk", "par": 90,
     "clue": "caesar", "events": ["storm", "kraken", "gold"]},
    {"grid": LEVEL_5, "monster_mode": "chase", "monster_speed": 100,
     "name": "Dead Man's Lagoon", "mood": "night", "par": 110,
     "clue": "crossing", "events": ["kraken", "gold", "storm"]},
]

SECRET = {"grid": SECRET_GRID, "monster_mode": "mix", "monster_speed": 95,
          "name": "Skull Cove", "mood": "cove", "par": 100,
          "clue": None, "events": ["storm", "kraken"], "secret": True}
