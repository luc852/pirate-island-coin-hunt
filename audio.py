"""Sound. Every call here is safe to make with no audio device at all.

The files come from make_sounds.py. A missing mixer, a missing file or a browser
that refuses to play anything all degrade to silence rather than to a crash:
the game was silent for its whole first life and still has to work that way.
"""
import os

import pygame

SOUNDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sounds")

VOLUMES = {
    "shanty": 0.34, "drone": 0.5, "waves": 0.30, "rain": 0.45,
    "coin1": 0.45, "coin2": 0.45, "coin3": 0.45, "coin4": 0.45, "coin5": 0.45,
    "click": 0.5, "tally": 0.4, "thunder": 0.8, "kraken": 0.8,
}
DEFAULT_VOLUME = 0.6

# Three looping beds on reserved channels; effects share the rest.
MUSIC, SEA, WEATHER = 0, 1, 2


class Audio:
    def __init__(self):
        self.ok = False
        self.muted = False
        self.sounds = {}
        self.playing = {}          # channel index -> loop name
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.set_num_channels(16)
            pygame.mixer.set_reserved(3)
            self.ok = True
        except Exception:
            return
        try:
            names = [f[:-4] for f in os.listdir(SOUNDS_DIR) if f.endswith(".wav")]
        except OSError:
            names = []
        for name in names:
            try:
                snd = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, name + ".wav"))
                snd.set_volume(VOLUMES.get(name, DEFAULT_VOLUME))
                self.sounds[name] = snd
            except Exception:
                pass
        # One line in the browser console, for diagnosing a silent build.
        self.report = (f"audio: {len(self.sounds)}/{len(names)} sounds loaded, "
                       f"mixer {pygame.mixer.get_init()}")
        try:
            import platform
            platform.window.console.log(self.report)
        except Exception:
            pass

    def play(self, name):
        if not self.ok or self.muted:
            return
        snd = self.sounds.get(name)
        if snd is not None:
            try:
                snd.play()
            except Exception:
                pass

    def loop(self, channel, name, fade_ms=600):
        """Make `name` the loop on a reserved channel (None stops it)."""
        if not self.ok or self.playing.get(channel) == name:
            return
        self.playing[channel] = name
        try:
            ch = pygame.mixer.Channel(channel)
            if name is None or name not in self.sounds:
                ch.fadeout(fade_ms)
                return
            ch.play(self.sounds[name], loops=-1, fade_ms=fade_ms)
            ch.set_volume(0.0 if self.muted else 1.0)
        except Exception:
            pass

    def toggle_mute(self):
        self.muted = not self.muted
        if self.ok:
            try:
                for channel in (MUSIC, SEA, WEATHER):
                    pygame.mixer.Channel(channel).set_volume(0.0 if self.muted else 1.0)
                if self.muted:
                    for i in range(3, pygame.mixer.get_num_channels()):
                        pygame.mixer.Channel(i).stop()
            except Exception:
                pass
        return self.muted
