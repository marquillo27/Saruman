"""
One-time script — generates chiptune SFX as WAV files.
Run from project root:  uv run python tools/generate_sfx.py
Creates 8 files in assets/audio/sfx/
"""
from __future__ import annotations

import os
import struct
import wave

ROOT = os.path.dirname(os.path.dirname(__file__))
RATE = 44100


def _sq(freq: float, dur: float, vol: float = 0.5) -> list[int]:
    """Square-wave with short attack/release envelope."""
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


def _noise(dur: float, vol: float = 0.4) -> list[int]:
    """White noise burst with fade-out envelope."""
    import random
    n   = int(RATE * dur)
    amp = int(32767 * vol)
    out: list[int] = []
    for i in range(n):
        env = 1.0 - (i / n)
        out.append(int(random.randint(-amp, amp) * env))
    return out


def _mix(*tracks: list[int]) -> list[int]:
    n = max(len(t) for t in tracks)
    out: list[int] = []
    for i in range(n):
        val = sum(t[i] if i < len(t) else 0 for t in tracks)
        out.append(max(-32768, min(32767, val)))
    return out


def _rest(dur: float) -> list[int]:
    return [0] * int(RATE * dur)


def _wav(path: str, samples: list[int]) -> None:
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))


# ---------------------------------------------------------------------------
# SFX builders
# ---------------------------------------------------------------------------

def build_jump() -> list[int]:
    """Short ascending chirp — player jumps."""
    return (
        _sq(300, 0.03, 0.5) +
        _sq(400, 0.03, 0.5) +
        _sq(550, 0.04, 0.4)
    )


def build_land() -> list[int]:
    """Quick low thud — player lands."""
    return _mix(
        _sq(80,  0.06, 0.6),
        _noise(0.04, 0.3),
    )


def build_coin() -> list[int]:
    """Bright rising two-note chime — coin/heart pickup."""
    return (
        _sq(660, 0.05, 0.45) + _rest(0.01) +
        _sq(880, 0.07, 0.45)
    )


def build_shoot() -> list[int]:
    """Short descending pew — player fires."""
    return (
        _sq(500, 0.02, 0.4) +
        _sq(380, 0.03, 0.35) +
        _sq(260, 0.02, 0.25)
    )


def build_hit() -> list[int]:
    """Buzzy low thud — player takes damage."""
    return _mix(
        _sq(120, 0.10, 0.55),
        _noise(0.07, 0.35),
    )


def build_stomp() -> list[int]:
    """Mid-freq impact — stomp on enemy (non-lethal)."""
    return _mix(
        _sq(200, 0.06, 0.5),
        _sq(150, 0.08, 0.35),
        _noise(0.04, 0.2),
    )


def build_enemy_death() -> list[int]:
    """Descending three-note burst — enemy dies."""
    return (
        _sq(440, 0.04, 0.5) +
        _sq(330, 0.04, 0.45) +
        _sq(220, 0.07, 0.4)
    )


def build_level_complete() -> list[int]:
    """Ascending 4-note arpeggio fanfare — level complete."""
    return (
        _sq(262, 0.08, 0.5) + _rest(0.02) +
        _sq(330, 0.08, 0.5) + _rest(0.02) +
        _sq(392, 0.08, 0.5) + _rest(0.02) +
        _sq(524, 0.18, 0.5)
    )


def build_shield_block() -> list[int]:
    """Metallic clank — projectile blocked by shield."""
    return _mix(
        _sq(300, 0.04, 0.5),
        _sq(180, 0.06, 0.4),
        _noise(0.03, 0.2),
    )


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    sfx_dir = os.path.join(ROOT, "assets", "audio", "sfx")
    os.makedirs(sfx_dir, exist_ok=True)

    sfx = [
        ("jump.wav",          build_jump),
        ("land.wav",          build_land),
        ("coin.wav",          build_coin),
        ("shoot.wav",         build_shoot),
        ("hit.wav",           build_hit),
        ("stomp.wav",         build_stomp),
        ("enemy_death.wav",   build_enemy_death),
        ("level_complete.wav",build_level_complete),
        ("shield_block.wav",  build_shield_block),
    ]

    print(f"Writing SFX to {sfx_dir}/")
    for filename, builder in sfx:
        samples = builder()
        path = os.path.join(sfx_dir, filename)
        _wav(path, samples)
        secs = len(samples) / RATE
        print(f"  {filename}: {secs:.2f}s")

    print(f"Done — {len(sfx)} SFX written.")


if __name__ == "__main__":
    main()
