"""Tests for the fixed-timestep accumulator driving the main loop."""
from __future__ import annotations

import pytest

from saruman.core.game import MAX_STEPS, STEP, fixed_steps


def _run(frame_times: list[float]) -> int:
    acc, total = 0.0, 0
    for dt in frame_times:
        steps, acc = fixed_steps(acc, dt)
        total += steps
    return total


def test_one_step_per_60hz_frame():
    assert fixed_steps(0.0, STEP)[0] == 1


def test_whole_millisecond_ticks_average_to_60_steps_per_second():
    # Clock.tick() returns whole ms: 17, 17, 16, 17, 17, 16, ... ≈ 16.67 ms
    frames = [0.017, 0.017, 0.016] * 20
    assert _run(frames) == 60


def test_slow_frame_rate_runs_catch_up_steps():
    # 30 fps for one second still simulates one second of game time
    assert _run([1 / 30] * 30) == 60


def test_fast_frame_rate_skips_steps():
    # 120 fps: about every other frame runs a step
    assert _run([1 / 120] * 120) == pytest.approx(60, abs=1)


def test_long_stall_is_capped():
    steps, acc = fixed_steps(0.0, 2.0)
    assert steps == MAX_STEPS
    assert acc < STEP


def test_leftover_never_negative():
    _, acc = fixed_steps(0.0, STEP - 0.0005)
    assert acc >= -0.001
