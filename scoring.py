"""The points system.

The old game paid a flat 10 a coin and 50 an island, so every pirate who won
finished on exactly the same score. Here the same coins are worth more to a
pirate who chains them, plays clean, plays fast and solves the island's riddle,
and every point is filed under a category so the end screens can show where a
score actually came from.
"""

COIN_VALUE = 10
COMBO_WINDOW = 2.6        # seconds a chain stays alive between coins
COMBO_STEP = 3            # coins per multiplier step
MAX_MULT = 5

BOTTLE_VALUE = 25
CHEST_BASE = 200          # + 50 per island
FIRST_DIG_BONUS = 100     # found with the very first hole: the riddle was read
GOLD_CRAB_VALUE = 200
KRAKEN_BONUS = 150        # ride out the kraken untouched
RUNES_BONUS = 500
RUNES_CLEAN_BONUS = 250   # no wrong plate
VAULT_COIN_VALUE = 25
CROWN_VALUE = 1500
CLEAR_PER_ISLAND = 100
FLAWLESS_BONUS = 150
TIME_PER_SECOND = 3
LIFE_BONUS = 150

# Order the categories are listed in on the end screen.
CATEGORIES = [
    ("coins", "Coins"),
    ("combo", "Combo chains"),
    ("storm", "Storm plunder"),
    ("treasure", "Buried treasure"),
    ("enigma", "Riddles solved"),
    ("events", "Sea encounters"),
    ("clear", "Islands cleared"),
    ("time", "Swift sailing"),
    ("flawless", "Untouched"),
    ("lives", "Lives to spare"),
    ("secret", "The Dread Crown"),
]

RANKS = [
    (0, "Deck Swabber"),
    (800, "Powder Monkey"),
    (2000, "Bosun"),
    (3500, "Quartermaster"),
    (5000, "Captain"),
    (7000, "Dread Captain"),
]
LEGEND_RANK = "Pirate Legend"


def rank_for(score, legend=False):
    if legend:
        return LEGEND_RANK
    title = RANKS[0][1]
    for floor, name in RANKS:
        if score >= floor:
            title = name
    return title


def multiplier_for(chain):
    return min(MAX_MULT, 1 + chain // COMBO_STEP)


class ScoreKeeper:
    def __init__(self):
        self.total = 0
        self.by_category = {key: 0 for key, _ in CATEGORIES}
        self.chain = 0
        self.chain_t = 0.0
        self.best_chain = 0
        self.islands_cleared = 0
        self.fragments = 0
        self.legend = False
        self.start_level()

    # ------------------------------------------------------------ per level
    def start_level(self):
        self.level_time = 0.0
        self.level_hits = 0
        self.level_best_chain = 0
        self.level_start_total = self.total
        self.chain = 0
        self.chain_t = 0.0

    def add(self, category, points):
        points = int(points)
        self.by_category[category] += points
        self.total += points
        return points

    @property
    def multiplier(self):
        return multiplier_for(self.chain)

    @property
    def chain_left(self):
        """0..1, how much of the combo window remains."""
        return max(0.0, self.chain_t / COMBO_WINDOW) if self.chain else 0.0

    def tick(self, dt):
        """Advance the level clock and the chain. Returns True if a chain of
        any worth just lapsed."""
        self.level_time += dt
        if self.chain:
            self.chain_t -= dt
            if self.chain_t <= 0:
                lapsed = self.chain >= COMBO_STEP
                self.chain = 0
                return lapsed
        return False

    def break_chain(self):
        self.chain = 0
        self.chain_t = 0.0

    def coin(self, storm=False, value=COIN_VALUE):
        """Bank one coin. Returns (points, multiplier, stepped_up)."""
        before = self.multiplier
        self.chain += 1
        self.chain_t = COMBO_WINDOW
        self.best_chain = max(self.best_chain, self.chain)
        self.level_best_chain = max(self.level_best_chain, self.chain)
        mult = self.multiplier
        self.add("coins", value)
        gained = value
        if mult > 1:
            gained += self.add("combo", value * (mult - 1))
        if storm:
            gained += self.add("storm", value * mult)
        return gained, mult, mult > before

    def hit(self):
        self.level_hits += 1
        self.break_chain()

    # ------------------------------------------------------------ bonuses
    def finish_level(self, island_number, par, secret=False):
        """Bank the end-of-island bonuses. Returns [(label, points), ...]
        beginning with what was earned while playing."""
        earned = self.total - self.level_start_total
        lines = [("Plunder on the island", earned)]
        self.islands_cleared += 1
        if not secret:      # the cove pays out through its crown instead
            lines.append(("Island cleared",
                          self.add("clear", CLEAR_PER_ISLAND * island_number)))
        left = par - self.level_time
        if left > 0:
            lines.append((f"Swift sailing ({int(left)}s under par)",
                          self.add("time", int(left) * TIME_PER_SECOND)))
        if self.level_hits == 0:
            lines.append(("Untouched", self.add("flawless", FLAWLESS_BONUS)))
        if self.level_best_chain >= COMBO_STEP:
            lines.append((f"Longest chain x{self.level_best_chain}",
                          self.add("combo", self.level_best_chain * 10)))
        return lines

    def finish_run(self, won, lives):
        if won and lives > 0:
            self.add("lives", lives * LIFE_BONUS)

    def breakdown(self):
        """[(label, points)] for every category that scored."""
        return [(label, self.by_category[key]) for key, label in CATEGORIES
                if self.by_category[key]]

    def summary(self):
        return {
            "islands": self.islands_cleared,
            "fragments": self.fragments,
            "legend": self.legend,
            "best_chain": self.best_chain,
            "rank": rank_for(self.total, self.legend),
        }
