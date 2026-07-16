"""Tests for the CreditsState scrolling credits screen."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from saruman.config import INTERNAL_H, INTERNAL_W
from saruman.core.state import StateStack
from saruman.states.credits import CreditsState, _LINES, _SCROLL_SPEED, _TOTAL_FRAMES


class _MockGame:
    def __init__(self) -> None:
        self.states = StateStack()


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.fixture
def game() -> _MockGame:
    return _MockGame()


@pytest.fixture
def credits_state(game) -> CreditsState:
    cs = CreditsState(game, score=1234)
    game.states._stack.append(cs)  # put it on the stack without triggering on_enter
    return cs


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

def test_done_starts_false(credits_state):
    assert credits_state._done is False


def test_frame_starts_zero(credits_state):
    assert credits_state._frame == 0


def test_scroll_starts_at_internal_h(credits_state):
    assert credits_state._scroll == float(INTERNAL_H)


def test_score_stored(credits_state):
    assert credits_state._score == 1234


# ---------------------------------------------------------------------------
# Pre-rendered lines
# ---------------------------------------------------------------------------

def test_rendered_length_matches_lines(credits_state):
    assert len(credits_state._rendered) == len(_LINES)


def test_gap_lines_have_none_surface(credits_state):
    for (text, kind), (surf, _h) in zip(_LINES, credits_state._rendered):
        if kind == "gap" or not text:
            assert surf is None


def test_total_height_is_positive(credits_state):
    assert credits_state._total_h > 0


def test_total_height_equals_sum_of_heights(credits_state):
    expected = sum(h for _, h in credits_state._rendered)
    assert credits_state._total_h == expected


# ---------------------------------------------------------------------------
# Scroll and frame counter
# ---------------------------------------------------------------------------

def test_update_decrements_scroll(credits_state):
    before = credits_state._scroll
    credits_state.update(1 / 60)
    assert abs(credits_state._scroll - (before - _SCROLL_SPEED)) < 0.001


def test_update_increments_frame(credits_state):
    before = credits_state._frame
    credits_state.update(1 / 60)
    assert credits_state._frame == before + 1


def test_update_noop_when_done(credits_state):
    credits_state._done = True
    credits_state._frame = 0
    credits_state.update(1 / 60)
    assert credits_state._frame == 0   # no increment


# ---------------------------------------------------------------------------
# Skip keys
# ---------------------------------------------------------------------------

def _key_event(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode="")


def test_return_key_advances(game):
    cs = CreditsState(game, score=0)
    game.states._stack.append(cs)
    cs.handle_event(_key_event(pygame.K_RETURN))
    assert cs._done is True


def test_space_key_advances(game):
    cs = CreditsState(game, score=0)
    game.states._stack.append(cs)
    cs.handle_event(_key_event(pygame.K_SPACE))
    assert cs._done is True


def test_escape_key_advances(game):
    cs = CreditsState(game, score=0)
    game.states._stack.append(cs)
    cs.handle_event(_key_event(pygame.K_ESCAPE))
    assert cs._done is True


def test_other_key_does_not_advance(credits_state):
    credits_state.handle_event(_key_event(pygame.K_LEFT))
    assert credits_state._done is False


# ---------------------------------------------------------------------------
# Auto-advance
# ---------------------------------------------------------------------------

def test_auto_advances_at_total_frames(game):
    cs = CreditsState(game, score=0)
    game.states._stack.append(cs)
    cs._frame = _TOTAL_FRAMES - 1
    cs.update(1 / 60)
    assert cs._done is True


def test_auto_advances_when_text_scrolls_off(game):
    cs = CreditsState(game, score=0)
    game.states._stack.append(cs)
    cs._scroll = -cs._total_h - 1.0   # all text above top of screen
    cs.update(1 / 60)
    assert cs._done is True


# ---------------------------------------------------------------------------
# Double-fire guard
# ---------------------------------------------------------------------------

def test_advance_idempotent(game):
    cs = CreditsState(game, score=0)
    game.states._stack.append(cs)
    cs._advance()
    first_state = game.states.current
    cs._advance()   # second call must not crash or replace again
    assert game.states.current is first_state


def test_done_set_after_advance(game):
    cs = CreditsState(game, score=0)
    game.states._stack.append(cs)
    cs._advance()
    assert cs._done is True


# ---------------------------------------------------------------------------
# Routing to GameOverState
# ---------------------------------------------------------------------------

def test_advance_routes_to_gameover(game):
    from saruman.states.gameover import GameOverState
    cs = CreditsState(game, score=500)
    game.states._stack.append(cs)
    cs._advance()
    assert isinstance(game.states.current, GameOverState)


def test_advance_passes_won_true(game):
    from saruman.states.gameover import GameOverState
    cs = CreditsState(game, score=500)
    game.states._stack.append(cs)
    cs._advance()
    go = game.states.current
    assert isinstance(go, GameOverState)
    assert go._won is True


def test_advance_passes_score(game):
    from saruman.states.gameover import GameOverState
    cs = CreditsState(game, score=9999)
    game.states._stack.append(cs)
    cs._advance()
    go = game.states.current
    assert isinstance(go, GameOverState)
    assert go._score == 9999


# ---------------------------------------------------------------------------
# draw() — no crash at various positions
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("scroll", [INTERNAL_H, 0.0, -50.0, -500.0])
def test_draw_does_not_crash(credits_state, scroll):
    surf = pygame.Surface((INTERNAL_W, INTERNAL_H))
    credits_state._scroll = scroll
    credits_state.draw(surf)


def test_hint_visible_at_frame_zero(credits_state):
    """Hint surface is rendered when frame < _TOTAL_FRAMES - 60."""
    credits_state._frame = 0
    surf = pygame.Surface((INTERNAL_W, INTERNAL_H))
    credits_state.draw(surf)   # just checking no exception


def test_draws_below_is_false():
    assert CreditsState.draws_below is False
