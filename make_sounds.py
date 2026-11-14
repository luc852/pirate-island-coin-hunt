"""Synthesize every sound in the game into assets/sounds/*.wav.

    python make_sounds.py        (needs numpy; the game itself does not)

Nothing here is sampled or downloaded: the effects, the sea, the rain and the
shanty are all built from sines, saws and filtered noise, so the audio carries
no licence of its own. The .wav files are committed, so this only needs to be
run again when a sound is changed. It is not part of running or building the
game.
"""
import os
import wave

import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sounds")
SR = 22050
rng = np.random.default_rng(7)


def save(name, x, sr=SR, peak=0.85):
    x = np.asarray(x, dtype=np.float64)
    m = np.max(np.abs(x)) or 1.0
    pcm = (x / m * peak * 32767).astype("<i2")
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(pcm.tobytes())
    print(f"{name:12s} {len(pcm) / sr:5.2f}s {len(pcm) * 2 / 1024:6.0f} KB")


def t(dur, sr=SR):
    return np.arange(int(dur * sr)) / sr


def env(n, attack=0.005, decay=6.0, sr=SR):
    x = np.arange(n) / sr
    return np.minimum(1.0, x / max(attack, 1e-6)) * np.exp(-decay * x)


def bell(freq, dur, decay=9.0, sr=SR):
    x = t(dur, sr)
    s = (np.sin(2 * np.pi * freq * x) + 0.45 * np.sin(2 * np.pi * freq * 2.01 * x)
         + 0.2 * np.sin(2 * np.pi * freq * 3.02 * x))
    return s * env(len(x), 0.003, decay, sr)


def shaped_noise(dur, lo, hi, sr=SR, tilt=0.0):
    """Band-limited noise built in the frequency domain, so it is exactly
    periodic over `dur` and loops without a click."""
    n = int(dur * sr)
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / sr)
    gain = ((f >= lo) & (f <= hi)).astype(float)
    if tilt:
        gain *= np.power(np.maximum(f, 1.0), -tilt)
    return np.fft.irfft(spec * gain, n)


def seq(parts, gap=0.0, sr=SR):
    """Lay (start_time, samples) pairs onto one buffer."""
    end = max(s + len(x) / sr for s, x in parts) + gap
    out = np.zeros(int(end * sr) + 1)
    for s, x in parts:
        i = int(s * sr)
        out[i:i + len(x)] += x
    return out


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


# ------------------------------------------------------------------ effects
def effects():
    # Coin: two-note chime, a step higher for each combo multiplier.
    for i in range(5):
        base = midi(83 + i * 2)
        save(f"coin{i + 1}", seq([(0.0, bell(base, 0.09, 14)),
                                  (0.06, bell(base * 4 / 3, 0.28, 11))]), peak=0.6)

    x = t(0.32)
    sweep = np.sign(np.sin(2 * np.pi * np.cumsum(220 * np.exp(-4 * x)) / SR))
    save("hit", (0.6 * sweep + shaped_noise(0.32, 200, 2500)) * env(len(x), 0.002, 9))

    scrape = shaped_noise(0.16, 900, 5000) * env(int(0.16 * SR), 0.02, 16)
    save("dig", seq([(0.0, scrape), (0.13, scrape * 0.7)]), peak=0.6)

    x = t(0.3)
    save("thud", np.sin(2 * np.pi * 95 * x) * env(len(x), 0.002, 12)
         + 0.4 * shaped_noise(0.3, 300, 1800) * env(len(x), 0.001, 40))

    notes = [72, 76, 79, 84, 88]
    save("chest", seq([(i * 0.09, bell(midi(n), 0.6 if i == 4 else 0.25, 5 if i == 4 else 9))
                       for i, n in enumerate(notes)]))

    save("bottle", seq([(0.0, bell(2100, 0.2, 22)), (0.0, bell(3170, 0.15, 30)),
                        (0.12, bell(2480, 0.3, 14))]), peak=0.55)

    x = t(2.2, 11025)
    rumble = shaped_noise(2.2, 25, 420, 11025, tilt=0.6)
    shape = np.exp(-1.6 * x) * (1 + 0.6 * np.sin(2 * np.pi * 5 * x) * np.exp(-2 * x))
    crack = shaped_noise(2.2, 400, 3500, 11025) * np.exp(-18 * x)
    save("thunder", rumble * shape * np.minimum(1, x / 0.01) + 0.5 * crack, sr=11025)

    x = t(0.4)
    save("splash", shaped_noise(0.4, 500, 6000) * env(len(x), 0.01, 9)
         * (1 + 0.5 * np.sin(2 * np.pi * 30 * x)), peak=0.6)

    x = t(1.5, 11025)
    f = 52 + 10 * np.sin(2 * np.pi * 3.1 * x)
    growl = 2 * ((np.cumsum(f) / 11025) % 1) - 1
    growl = growl * (1 + 0.5 * np.sin(2 * np.pi * 23 * x))
    growl += 0.5 * shaped_noise(1.5, 60, 500, 11025)
    save("kraken", growl * np.sin(np.pi * x / 1.5) ** 0.7, sr=11025)

    x = t(0.4)
    whoosh = shaped_noise(0.4, 300, 2600) * np.sin(np.pi * x / 0.4) ** 2
    save("tentacle", whoosh + seq([(0.22, np.sin(2 * np.pi * 70 * t(0.18))
                                    * env(int(0.18 * SR), 0.002, 18))])[:len(x)], peak=0.6)

    save("gold", seq([(i * 0.045, bell(midi(n), 0.3, 12))
                      for i, n in enumerate([84, 88, 91, 96, 91, 96, 100, 103])]), peak=0.6)

    save("rune_ok", seq([(0, bell(midi(69), 0.7, 5)), (0, bell(midi(76), 0.7, 5))]), peak=0.6)

    x = t(0.45)
    save("rune_bad", (np.sign(np.sin(2 * np.pi * 98 * x))
                      + np.sign(np.sin(2 * np.pi * 104 * x))) * env(len(x), 0.005, 6), peak=0.5)

    x = t(1.6, 11025)
    grind = shaped_noise(1.6, 30, 600, 11025, tilt=0.4) * np.sin(np.pi * x / 1.6)
    chord = sum(np.sin(2 * np.pi * midi(n) * x) for n in (50, 57, 62, 65)) * (x / 1.6) ** 2
    save("vault", grind + 0.25 * chord * np.minimum(1, (1.6 - x) / 0.1), sr=11025)

    def fanfare(notes, step, last):
        return seq([(i * step, bell(midi(n), last if i == len(notes) - 1 else step * 2.2,
                                    3.5 if i == len(notes) - 1 else 8))
                    for i, n in enumerate(notes)])

    save("clear", fanfare([74, 77, 81, 86, 81, 86], 0.11, 0.8))
    save("over", fanfare([74, 72, 69, 65, 62], 0.2, 1.1), peak=0.7)
    save("win", seq([(0, fanfare([74, 74, 77, 81, 86, 89, 93], 0.13, 1.4)),
                     (0.78, bell(midi(62), 1.4, 3)), (0.78, bell(midi(69), 1.4, 3))]))
    save("secret", seq([(0, fanfare([62, 69, 74, 77, 81, 86, 89, 93, 98], 0.14, 2.0)),
                        (1.12, bell(midi(50), 2.0, 2)), (1.12, bell(midi(57), 2.0, 2)),
                        (1.12, bell(midi(65), 2.0, 2))]))

    save("click", bell(1400, 0.05, 60), peak=0.4)
    save("tally", bell(midi(88), 0.09, 30), peak=0.45)
    save("combo", seq([(0, bell(midi(81), 0.08, 20)), (0.05, bell(midi(88), 0.2, 12))]), peak=0.5)
    save("bell", seq([(0, bell(midi(57), 1.6, 2.5)), (0.0, bell(midi(57) * 2.76, 1.0, 5))]), peak=0.6)


# -------------------------------------------------------------------- loops
def loops():
    sr = 11025
    # Surf: two swells of soft noise, phase-offset so it never falls silent.
    dur = 8.0
    x = t(dur, sr)
    low = shaped_noise(dur, 60, 900, sr, tilt=0.5)
    high = shaped_noise(dur, 900, 3800, sr, tilt=0.3)
    swell = 0.35 + 0.65 * (0.5 - 0.5 * np.cos(2 * np.pi * x / 4.0)) ** 2
    hiss = 0.2 + 0.8 * (0.5 - 0.5 * np.cos(2 * np.pi * (x - 0.9) / 4.0)) ** 3
    low /= np.max(np.abs(low))
    high /= np.max(np.abs(high))
    save("waves", low * swell + 0.6 * high * hiss, sr=sr, peak=0.7)

    rain = shaped_noise(4.0, 1200, 5000, sr)
    wind = shaped_noise(4.0, 80, 500, sr, tilt=0.5)
    x = t(4.0, sr)
    save("rain", rain / np.max(np.abs(rain))
         + 0.9 * wind / np.max(np.abs(wind)) * (0.6 + 0.4 * np.sin(2 * np.pi * x / 4.0)),
         sr=sr, peak=0.7)

    # The cove: a low drone with a slow beat, for the secret island.
    dur = 8.0
    x = t(dur, sr)
    drone = (np.sin(2 * np.pi * 73.5 * x) + 0.8 * np.sin(2 * np.pi * 73.75 * x)
             + 0.5 * np.sin(2 * np.pi * 110.25 * x) + 0.25 * np.sin(2 * np.pi * 147.0 * x)
             + 0.12 * np.sin(2 * np.pi * 220.5 * x) * (0.5 + 0.5 * np.sin(2 * np.pi * x / 8)))
    air = shaped_noise(dur, 200, 1200, sr, tilt=0.6)
    save("drone", drone + 1.5 * air / np.max(np.abs(air)), sr=sr, peak=0.6)

    shanty()


def shanty():
    """A 16-bar jig in D minor, 6/8. Original tune."""
    sr = 16000
    e = 0.2                       # one eighth note
    bar = 6 * e
    total = 16 * bar
    n_total = int(total * sr)
    out = np.zeros(n_total)

    def put(start, x, gain=1.0):
        i = int(start * sr) % n_total
        # Wrap tails round to the start so the loop point is seamless.
        idx = (i + np.arange(len(x))) % n_total
        np.add.at(out, idx, x * gain)

    def squeeze(freq, dur):       # concertina-ish lead
        x = t(dur + 0.12, sr)
        s = sum(np.sin(2 * np.pi * freq * k * x * (1 + d)) / k
                for k in range(1, 7) for d in (-0.003, 0.003))
        a = np.minimum(1, x / 0.02) * np.minimum(1, np.maximum(0, (dur + 0.12 - x) / 0.12))
        return s * a * (1 + 0.12 * np.sin(2 * np.pi * 5.5 * x))

    def pluck(freq, dur, decay=7):
        x = t(dur, sr)
        s = sum(np.sin(2 * np.pi * freq * k * x) / k ** 1.6 for k in range(1, 6))
        return s * env(len(x), 0.004, decay, sr)

    D4, E4, F4, G4, A4, Bb4, C5, Cs5 = 62, 64, 65, 67, 69, 70, 72, 73
    D5, E5, F5, G5, A5, Bb5, C6, D6 = 74, 76, 77, 79, 81, 82, 84, 86
    a_part = [
        [(D5, 2), (F5, 1), (A5, 2), (G5, 1)],
        [(F5, 2), (E5, 1), (D5, 3)],
        [(C5, 2), (E5, 1), (G5, 2), (F5, 1)],
        [(E5, 2), (D5, 1), (E5, 3)],
        [(D5, 2), (F5, 1), (A5, 2), (G5, 1)],
        [(A5, 2), (Bb5, 1), (A5, 3)],
        [(G5, 2), (F5, 1), (E5, 2), (Cs5, 1)],
        [(D5, 5), (None, 1)],
    ]
    b_part = [
        [(F5, 2), (A5, 1), (C6, 2), (A5, 1)],
        [(Bb5, 2), (A5, 1), (G5, 3)],
        [(E5, 2), (G5, 1), (Bb5, 2), (G5, 1)],
        [(A5, 2), (G5, 1), (A5, 3)],
        [(D5, 2), (F5, 1), (A5, 2), (D6, 1)],
        [(C6, 2), (Bb5, 1), (A5, 3)],
        [(G5, 2), (F5, 1), (E5, 2), (Cs5, 1)],
        [(D5, 5), (None, 1)],
    ]
    Dm, C, A, F, Gm = (38, 45, (62, 65, 69)), (36, 43, (60, 64, 67)), \
        (33, 40, (61, 64, 69)), (41, 48, (60, 65, 69)), (43, 50, (62, 67, 70))
    chords = [Dm, Dm, C, A, Dm, Dm, Gm, Dm, F, Gm, C, A, Dm, F, Gm, Dm]

    for b, notes in enumerate(a_part + b_part):
        pos = b * bar
        for note, length in notes:
            if note is not None:
                put(pos, squeeze(midi(note), length * e * 0.92), 0.16)
            pos += length * e
        root, fifth, triad = chords[b]
        if b % 8 == 6:            # the turnaround bar: Gm to A
            fifth = 45
        put(b * bar, pluck(midi(root), 0.55, 5), 0.9)
        put(b * bar + 3 * e, pluck(midi(fifth), 0.5, 5), 0.75)
        for k in (1, 2, 4, 5):
            for n in triad:
                put(b * bar + k * e, pluck(midi(n), 0.18, 16), 0.11)
        for k in range(6):        # shaker, with a foot-stomp on the two beats
            tick = shaped_noise(0.05, 3000, 7000, sr) * env(int(0.05 * sr), 0.001, 70, sr)
            put(b * bar + k * e, tick / np.max(np.abs(tick)), 0.10 if k % 3 else 0.2)
        for k in (0, 3):
            x = t(0.12, sr)
            put(b * bar + k * e, np.sin(2 * np.pi * 70 * x) * env(len(x), 0.002, 30, sr), 0.7)
    save("shanty", out, sr=sr, peak=0.8)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    effects()
    loops()
    print("total", sum(os.path.getsize(os.path.join(OUT, f))
                       for f in os.listdir(OUT)) // 1024, "KB")
