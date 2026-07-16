"""One-time script — generates placeholder audio assets.
Run from project root:  uv run python tools/generate_audio.py
Creates:
  assets/audio/music/menu.wav     — square-wave chiptune menu theme (8-bar loop)
  assets/audio/music/wolfwood.wav — darker in-game theme for Wolfwood (110 BPM, Am)
  assets/audio/music/caverns.wav  — eerie in-game theme for Glass Caverns (90 BPM)
"""
from __future__ import annotations

import os
import struct
import wave

ROOT = os.path.dirname(os.path.dirname(__file__))
RATE = 44100
BEAT = 60.0 / 140  # seconds per beat at 140 BPM

# ── note frequencies (Hz) ──────────────────────────────────────────────────
C3=130.81; D3=146.83; E3=164.81; F3=174.61; G3=196.00; A3=220.00
C4=261.63; D4=293.66; E4=329.63; F4=349.23; G4=392.00; A4=440.00
C5=523.25; D5=587.33; E5=659.25; G5=783.99; A5=880.00


def _sq(freq: float, dur: float, vol: float = 0.5) -> list[int]:
    """Square-wave samples with a short attack/release envelope to avoid clicks."""
    n = int(RATE * dur)
    if n == 0:
        return []
    period = RATE / freq
    fade   = max(1, min(int(RATE * 0.008), n // 4))
    amp    = int(32767 * vol)
    out: list[int] = []
    for i in range(n):
        raw = amp if (i % period) < (period / 2) else -amp
        env = min(1.0, min(i, n - 1 - i) / fade)
        out.append(int(raw * env))
    return out


def _rest(dur: float) -> list[int]:
    return [0] * int(RATE * dur)


def _mix(*tracks: list[int]) -> list[int]:
    n = max(len(t) for t in tracks)
    out: list[int] = []
    for i in range(n):
        val = sum(t[i] if i < len(t) else 0 for t in tracks)
        out.append(max(-32768, min(32767, val)))
    return out


def _wav(path: str, samples: list[int]) -> None:
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))


# ── Menu theme ─────────────────────────────────────────────────────────────
# 8-bar loop, 4/4 at 140 BPM.  Chord progression: C | Am | C | G | Am | C | F | G

def build_menu_theme() -> list[int]:
    b    = BEAT
    gate = 0.85  # note gate (fraction of beat that sounds)

    def n(freq: float | None, beats: float = 1.0) -> list[int]:
        if freq is None:
            return _rest(b * beats)
        snd = _sq(freq, b * beats * gate, 0.45)
        return snd + _rest(b * beats * (1 - gate))

    melody: list[int] = (
        # bar 1 — C
        n(E5) + n(G5) + n(A5) + n(G5) +
        # bar 2 — Am
        n(E5) + n(C5) + n(D5) + n(E5) +
        # bar 3 — C
        n(G5) + n(A5) + n(G5) + n(E5) +
        # bar 4 — G
        n(C5) + n(E5) + n(G5) + n(None) +
        # bar 5 — Am
        n(A5) + n(G5) + n(E5) + n(D5) +
        # bar 6 — C
        n(E5) + n(G5) + n(A5) + n(G5) +
        # bar 7 — F
        n(C5) + n(E5) + n(G5) + n(A5) +
        # bar 8 — G → C (hold last note 2 beats)
        n(G5) + n(E5) + n(C5, 2.0)
    )

    def bass_bar(root: float, fifth: float) -> list[int]:
        bg = 0.9
        def r(f: float) -> list[int]:
            return _sq(f, b * bg, 0.2) + _rest(b * (1 - bg))
        return r(root) + r(fifth) + r(root) + r(fifth)

    bass: list[int] = (
        bass_bar(C3, G3) +  # C
        bass_bar(A3, E3) +  # Am
        bass_bar(C3, G3) +  # C
        bass_bar(G3, D3) +  # G
        bass_bar(A3, E3) +  # Am
        bass_bar(C3, G3) +  # C
        bass_bar(F3, C3) +  # F
        bass_bar(G3, D3)    # G
    )

    return _mix(melody, bass)


# ── Wolfwood theme ──────────────────────────────────────────────────────────
# 8-bar loop, 4/4 at 110 BPM, Am minor — darker, slower than menu theme.
# Chord progression: Am | Em | Am | C | Dm | Am | Em | Am

def build_wolfwood_theme() -> list[int]:
    b    = 60.0 / 110
    gate = 0.80

    def n(freq: float | None, beats: float = 1.0) -> list[int]:
        if freq is None:
            return _rest(b * beats)
        snd = _sq(freq, b * beats * gate, 0.38)
        return snd + _rest(b * beats * (1 - gate))

    A4 = 440.00; E4 = 329.63; C4 = 261.63; D4 = 293.66
    A5 = 880.00; E5 = 659.25; C5 = 523.25; D5 = 587.33; G4 = 392.00

    melody: list[int] = (
        # bar 1 — Am
        n(A4) + n(C5) + n(E5) + n(A4) +
        # bar 2 — Em
        n(E4) + n(G4) + n(E5) + n(None) +
        # bar 3 — Am
        n(A4) + n(E5) + n(C5) + n(A4) +
        # bar 4 — C
        n(C5) + n(E5) + n(G4) + n(None) +
        # bar 5 — Dm
        n(D4) + n(A4) + n(D5) + n(A4) +
        # bar 6 — Am
        n(A4) + n(C5) + n(E5) + n(C5) +
        # bar 7 — Em
        n(E4) + n(G4) + n(E5) + n(None) +
        # bar 8 — Am (hold)
        n(A4) + n(None) + n(A4, 2.0)
    )

    A2 = 110.00; E2 = 82.41; C2 = 65.41; D2 = 73.42; G2 = 98.00

    def bass_bar(root: float, fifth: float) -> list[int]:
        bg = 0.88
        def r(f: float) -> list[int]:
            return _sq(f, b * bg, 0.22) + _rest(b * (1 - bg))
        return r(root) + r(fifth) + r(root) + r(fifth)

    bass: list[int] = (
        bass_bar(A2, E2) +  # Am
        bass_bar(E2, A2) +  # Em
        bass_bar(A2, E2) +  # Am
        bass_bar(C2, G2) +  # C
        bass_bar(D2, A2) +  # Dm
        bass_bar(A2, E2) +  # Am
        bass_bar(E2, A2) +  # Em
        bass_bar(A2, E2)    # Am
    )

    return _mix(melody, bass)


# ── Glass Caverns theme ─────────────────────────────────────────────────────
# 8-bar loop, 4/4 at 90 BPM — sparse, eerie, low register.
# Chord progression: Cm | Cm | Ab | Bb | Cm | Gm | Ab | Cm

def build_caverns_theme() -> list[int]:
    b    = 60.0 / 90
    gate = 0.75

    def n(freq: float | None, beats: float = 1.0) -> list[int]:
        if freq is None:
            return _rest(b * beats)
        snd = _sq(freq, b * beats * gate, 0.32)
        return snd + _rest(b * beats * (1 - gate))

    C4 = 261.63; Eb4 = 311.13; G4 = 392.00
    Ab4 = 415.30; Bb4 = 466.16; C3 = 130.81
    G3 = 196.00; Eb3 = 155.56

    melody: list[int] = (
        # bar 1-2 — Cm (sparse)
        n(C4) + n(None) + n(Eb4) + n(None) +
        n(G4) + n(None) + n(Eb4) + n(None) +
        # bar 3 — Ab
        n(Ab4) + n(None) + n(C4) + n(Eb4) +
        # bar 4 — Bb
        n(Bb4) + n(G4) + n(None) + n(None) +
        # bar 5 — Cm
        n(C4) + n(Eb4) + n(G4) + n(Eb4) +
        # bar 6 — Gm
        n(G3) + n(None) + n(Eb3) + n(G3) +
        # bar 7 — Ab
        n(Ab4) + n(None) + n(C4) + n(None) +
        # bar 8 — Cm (resolve)
        n(G4) + n(Eb4) + n(C4, 2.0)
    )

    C2 = 65.41; G2 = 98.00; Ab2 = 103.83; Bb2 = 116.54; G1 = 49.00; Eb2 = 77.78

    def bass_note(freq: float, beats: float = 2.0) -> list[int]:
        bg = 0.85
        snd = _sq(freq, b * beats * bg, 0.28)
        return snd + _rest(b * beats * (1 - bg))

    bass: list[int] = (
        bass_note(C2, 2.0) + bass_note(G2, 2.0) +   # Cm
        bass_note(C2, 2.0) + bass_note(Eb2, 2.0) +  # Cm
        bass_note(Ab2, 2.0) + bass_note(Eb2, 2.0) + # Ab
        bass_note(Bb2, 2.0) + bass_note(G2, 2.0) +  # Bb
        bass_note(C2, 2.0) + bass_note(G2, 2.0) +   # Cm
        bass_note(G1, 2.0) + bass_note(G2, 2.0) +   # Gm
        bass_note(Ab2, 2.0) + bass_note(C2, 2.0) +  # Ab
        bass_note(C2, 4.0)                           # Cm
    )

    return _mix(melody, bass)


# ── Greenshire Hills theme ──────────────────────────────────────────────────
# 8-bar loop, 4/4 at 130 BPM, C major — bright, playful tutorial.
# Progression: C | G | Am | F | C | G | F | C

def build_greenshire_theme() -> list[int]:
    b    = 60.0 / 130
    gate = 0.82

    def n(freq: float | None, beats: float = 1.0) -> list[int]:
        if freq is None:
            return _rest(b * beats)
        snd = _sq(freq, b * beats * gate, 0.42)
        return snd + _rest(b * beats * (1 - gate))

    E5=659.25; G5=783.99; A5=880.00; C5=523.25; D5=587.33; F5=698.46; B4=493.88

    melody: list[int] = (
        # bar 1 — C
        n(E5) + n(G5) + n(C5) + n(E5) +
        # bar 2 — G
        n(G5) + n(B4) + n(D5) + n(G5) +
        # bar 3 — Am
        n(A5) + n(E5) + n(C5) + n(A5) +
        # bar 4 — F
        n(F5) + n(A5) + n(C5) + n(None) +
        # bar 5 — C
        n(E5) + n(C5) + n(G5) + n(E5) +
        # bar 6 — G
        n(D5) + n(G5) + n(B4) + n(D5) +
        # bar 7 — F
        n(F5) + n(A5) + n(C5) + n(A5) +
        # bar 8 — C
        n(G5) + n(E5) + n(C5, 2.0)
    )

    C3=130.81; G3=196.00; A3=220.00; F3=174.61; D3=146.83; B2=123.47

    def bass_bar(root: float, fifth: float) -> list[int]:
        bg = 0.88
        def r(f: float) -> list[int]:
            return _sq(f, b * bg, 0.22) + _rest(b * (1 - bg))
        return r(root) + r(fifth) + r(root) + r(fifth)

    bass: list[int] = (
        bass_bar(C3, G3) +  # C
        bass_bar(G3, D3) +  # G
        bass_bar(A3, E3) +  # Am
        bass_bar(F3, C3) +  # F
        bass_bar(C3, G3) +  # C
        bass_bar(G3, D3) +  # G
        bass_bar(F3, C3) +  # F
        bass_bar(C3, G3)    # C
    )

    return _mix(melody, bass)


# ── Sunken Mines theme ──────────────────────────────────────────────────────
# 8-bar loop, 4/4 at 100 BPM, F minor — tense, rhythmic, underground.
# Progression: Fm | Fm | Db | Eb | Fm | Cm | Db | Eb

def build_mines_theme() -> list[int]:
    b    = 60.0 / 100
    gate = 0.78

    def n(freq: float | None, beats: float = 1.0) -> list[int]:
        if freq is None:
            return _rest(b * beats)
        snd = _sq(freq, b * beats * gate, 0.36)
        return snd + _rest(b * beats * (1 - gate))

    F4=349.23; Ab4=415.30; C4=261.63; Db4=277.18; Eb4=311.13; G4=392.00; Bb3=233.08

    melody: list[int] = (
        # bar 1-2 — Fm (driving repeating figure)
        n(F4) + n(Ab4) + n(C4) + n(Ab4) +
        n(F4) + n(None)+ n(Ab4)+ n(C4)  +
        # bar 3 — Db
        n(Db4)+ n(Ab4) + n(F4) + n(Ab4) +
        # bar 4 — Eb
        n(Eb4)+ n(G4)  + n(Bb3)+ n(None)+
        # bar 5 — Fm
        n(F4) + n(C4)  + n(Ab4)+ n(F4)  +
        # bar 6 — Cm
        n(C4) + n(Eb4) + n(G4) + n(Eb4) +
        # bar 7 — Db
        n(Db4)+ n(F4)  + n(Ab4)+ n(None)+
        # bar 8 — Eb → Fm
        n(Eb4)+ n(G4)  + n(F4, 2.0)
    )

    F2=87.31; Ab2=103.83; Db2=69.30; Eb2=77.78; C2=65.41; G2=98.00

    def bass_pulse(root: float) -> list[int]:
        bg = 0.75
        def r(f: float) -> list[int]:
            return _sq(f, b * bg, 0.30) + _rest(b * (1 - bg))
        return r(root) + r(root) + r(root) + r(root)

    bass: list[int] = (
        bass_pulse(F2) +   # Fm
        bass_pulse(F2) +   # Fm
        bass_pulse(Db2) +  # Db
        bass_pulse(Eb2) +  # Eb
        bass_pulse(F2) +   # Fm
        bass_pulse(C2) +   # Cm
        bass_pulse(Db2) +  # Db
        bass_pulse(Eb2)    # Eb
    )

    return _mix(melody, bass)


# ── Ash Marshes theme ───────────────────────────────────────────────────────
# 8-bar loop, 4/4 at 95 BPM, D minor — haunting, swampy, eerie.
# Progression: Dm | Am | Bb | C | Dm | Gm | A | Dm

def build_marshes_theme() -> list[int]:
    b    = 60.0 / 95
    gate = 0.72

    def n(freq: float | None, beats: float = 1.0) -> list[int]:
        if freq is None:
            return _rest(b * beats)
        snd = _sq(freq, b * beats * gate, 0.34)
        return snd + _rest(b * beats * (1 - gate))

    D4=293.66; F4=349.23; A4=440.00; E4=329.63; Bb4=466.16; C4=261.63; G4=392.00

    melody: list[int] = (
        # bar 1 — Dm
        n(D4) + n(None)+ n(F4) + n(A4)  +
        # bar 2 — Am
        n(A4) + n(E4)  + n(None)+ n(A4) +
        # bar 3 — Bb
        n(Bb4)+ n(F4)  + n(D4) + n(None)+
        # bar 4 — C
        n(C4) + n(E4)  + n(G4) + n(None)+
        # bar 5 — Dm
        n(D4) + n(F4)  + n(A4) + n(F4)  +
        # bar 6 — Gm
        n(G4) + n(None)+ n(D4) + n(G4)  +
        # bar 7 — A (dominant)
        n(A4) + n(E4)  + n(None)+ n(A4) +
        # bar 8 — Dm (resolve)
        n(D4) + n(F4)  + n(D4, 2.0)
    )

    D2=73.42; A2=110.00; Bb2=116.54; C2=65.41; G2=98.00; E2=82.41

    def bass_bar_m(root: float, fifth: float) -> list[int]:
        bg = 0.86
        def r(f: float) -> list[int]:
            return _sq(f, b * bg, 0.24) + _rest(b * (1 - bg))
        return r(root) + r(fifth) + r(root) + r(fifth)

    bass: list[int] = (
        bass_bar_m(D2, A2)  +  # Dm
        bass_bar_m(A2, E2)  +  # Am
        bass_bar_m(Bb2, F3) +  # Bb
        bass_bar_m(C2, G2)  +  # C
        bass_bar_m(D2, A2)  +  # Dm
        bass_bar_m(G2, D2)  +  # Gm
        bass_bar_m(A2, E2)  +  # A
        bass_bar_m(D2, A2)     # Dm
    )

    return _mix(melody, bass)


# ── Pale Tower theme ────────────────────────────────────────────────────────
# 8-bar loop, 4/4 at 120 BPM, E minor — epic, driving, final boss.
# Progression: Em | C | G | D | Em | Am | C | B→Em

def build_tower_theme() -> list[int]:
    b    = 60.0 / 120
    gate = 0.84

    def n(freq: float | None, beats: float = 1.0) -> list[int]:
        if freq is None:
            return _rest(b * beats)
        snd = _sq(freq, b * beats * gate, 0.40)
        return snd + _rest(b * beats * (1 - gate))

    E5=659.25; G5=783.99; B4=493.88; C5=523.25; D5=587.33; A4=440.00; F5=698.46

    melody: list[int] = (
        # bar 1 — Em
        n(E5) + n(B4) + n(G5) + n(E5) +
        # bar 2 — C
        n(C5) + n(E5) + n(G5) + n(C5) +
        # bar 3 — G
        n(G5) + n(D5) + n(B4) + n(G5) +
        # bar 4 — D
        n(D5) + n(F5) + n(A4) + n(None)+
        # bar 5 — Em (more urgent)
        n(E5) + n(G5) + n(B4) + n(E5) +
        # bar 6 — Am
        n(A4) + n(C5) + n(E5) + n(A4) +
        # bar 7 — C
        n(C5) + n(E5) + n(G5) + n(None)+
        # bar 8 — B → Em (dramatic resolve)
        n(B4) + n(D5) + n(E5, 2.0)
    )

    E2=82.41; G2=98.00; C2=65.41; D2=73.42; A2=110.00; B2=123.47

    def bass_bar_t(root: float, fifth: float) -> list[int]:
        bg = 0.90
        def r(f: float) -> list[int]:
            return _sq(f, b * bg, 0.26) + _rest(b * (1 - bg))
        return r(root) + r(fifth) + r(root) + r(fifth)

    bass: list[int] = (
        bass_bar_t(E2, B2) +  # Em
        bass_bar_t(C2, G2) +  # C
        bass_bar_t(G2, D2) +  # G
        bass_bar_t(D2, A2) +  # D
        bass_bar_t(E2, B2) +  # Em
        bass_bar_t(A2, E2) +  # Am
        bass_bar_t(C2, G2) +  # C
        bass_bar_t(B2, E2)    # B→Em
    )

    return _mix(melody, bass)


def main() -> None:
    music_dir = os.path.join(ROOT, "assets", "audio", "music")
    os.makedirs(music_dir, exist_ok=True)

    tracks = [
        ("menu.wav",        build_menu_theme),
        ("wolfwood.wav",    build_wolfwood_theme),
        ("caverns.wav",     build_caverns_theme),
        ("greenshire.wav",  build_greenshire_theme),
        ("mines.wav",       build_mines_theme),
        ("marshes.wav",     build_marshes_theme),
        ("tower.wav",       build_tower_theme),
    ]
    for filename, builder in tracks:
        samples = builder()
        path = os.path.join(music_dir, filename)
        _wav(path, samples)
        secs = len(samples) / RATE
        print(f"  {filename}: {secs:.1f}s, {len(samples) * 2 // 1024} kB")
    print("Done.")


if __name__ == "__main__":
    main()
