from __future__ import annotations

import pygame

from saruman.paths import asset_path

_instance: AudioManager | None = None


class AudioManager:
    def __init__(self) -> None:
        self._music_name: str | None = None
        self._music_vol  = 0.6
        self._sfx_vol    = 0.5
        self._sfx_cache: dict[str, pygame.mixer.Sound | None] = {}

    # ------------------------------------------------------------------

    def set_music_volume(self, vol_0_10: int) -> None:
        self._music_vol = vol_0_10 / 10.0
        try:
            pygame.mixer.music.set_volume(self._music_vol)
        except pygame.error:
            pass

    def set_sfx_volume(self, vol_0_10: int) -> None:
        self._sfx_vol = vol_0_10 / 10.0
        for snd in self._sfx_cache.values():
            if snd:
                snd.set_volume(self._sfx_vol)

    # ------------------------------------------------------------------

    def play_music(self, name: str, loops: int = -1) -> None:
        if self._music_name == name:
            return
        self._music_name = name
        candidates = [name]
        if name.endswith(".ogg"):
            candidates.append(name[:-4] + ".wav")
        for candidate in candidates:
            try:
                path = asset_path("audio", "music", candidate)
                pygame.mixer.music.load(str(path))
                pygame.mixer.music.set_volume(self._music_vol)
                pygame.mixer.music.play(loops)
                return
            except (pygame.error, FileNotFoundError, OSError):
                pass

    def stop_music(self) -> None:
        self._music_name = None
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass

    def play_sfx(self, name: str) -> None:
        if name not in self._sfx_cache:
            path = asset_path("audio", "sfx", name)
            try:
                self._sfx_cache[name] = pygame.mixer.Sound(str(path))
            except (pygame.error, FileNotFoundError, OSError):
                self._sfx_cache[name] = None
        snd = self._sfx_cache[name]
        if snd:
            snd.set_volume(self._sfx_vol)
            snd.play()


def get_audio() -> AudioManager:
    global _instance
    if _instance is None:
        _instance = AudioManager()
    return _instance
