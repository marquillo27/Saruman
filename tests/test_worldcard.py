"""Tests for the WorldCardState world intro cards."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from saruman.config import INTERNAL_H, INTERNAL_W
from saruman.core.state import State, StateStack
from saruman.states.worldcard import WORLDS, WorldCardState


class _MockGame:
    def __init__(self) -> None:
        self.states = StateStack()


class _Sentinel(State):
    """Stand-in for the level the factory hands off to."""


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.fixture
def game() -> _MockGame:
    return _MockGame()


def _make(game, stem="level_01_greenshire_hills"):
    sentinel = _Sentinel()
    card = WorldCardState(game, stem, lambda: sentinel)
    game.states._stack.append(card)
    return card, sentinel


def _key_event(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode="")


# ---------------------------------------------------------------------------
# WORLDS table — one card per world, keyed by each world's first level
# ---------------------------------------------------------------------------

def test_worlds_has_three_entries():
    assert len(WORLDS) == 3


def test_worlds_keys_are_world_first_stems():
    assert set(WORLDS) == {
        "level_01_greenshire_hills",
        "level_11_ashfall_wastes",
        "level_06_pale_tower",
    }


@pytest.mark.parametrize("stem", list(WORLDS))
def test_world_entry_shape(stem):
    sub, title, accent, bg = WORLDS[stem]
    assert isinstance(sub, str) and sub
    assert isinstance(title, str) and title
    assert len(accent) == 3
    assert len(bg) == 3


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

def test_done_starts_false(game):
    card, _ = _make(game)
    assert card._done is False


def test_frame_starts_zero(game):
    card, _ = _make(game)
    assert card._frame == 0


@pytest.mark.parametrize("stem", list(WORLDS))
def test_constructs_for_each_world(game, stem):
    card, _ = _make(game, stem)
    assert card._title_surf.get_width() > 0


# ---------------------------------------------------------------------------
# Update / auto-advance
# ---------------------------------------------------------------------------

def test_update_increments_frame(game):
    card, _ = _make(game)
    card.update(1 / 60)
    assert card._frame == 1


def test_auto_advances_after_full_duration(game):
    card, sentinel = _make(game)
    card._frame = WorldCardState.FADE * 2 + WorldCardState.HOLD - 1
    card.update(1 / 60)
    assert card._done is True
    assert game.states.current is sentinel


def test_update_noop_when_done(game):
    card, _ = _make(game)
    card._done = True
    card._frame = 0
    card.update(1 / 60)
    assert card._frame == 0


# ---------------------------------------------------------------------------
# Skip keys
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", [pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE])
def test_skip_keys_advance(game, key):
    card, sentinel = _make(game)
    card.handle_event(_key_event(key))
    assert card._done is True
    assert game.states.current is sentinel


def test_other_key_does_not_advance(game):
    card, _ = _make(game)
    card.handle_event(_key_event(pygame.K_LEFT))
    assert card._done is False


# ---------------------------------------------------------------------------
# Hand-off routing
# ---------------------------------------------------------------------------

def test_advance_routes_to_factory_result(game):
    card, sentinel = _make(game)
    card._advance()
    assert game.states.current is sentinel


def test_advance_idempotent(game):
    card, _ = _make(game)
    card._advance()
    first = game.states.current
    card._advance()
    assert game.states.current is first


# ---------------------------------------------------------------------------
# draw() — no crash through fade-in, hold, fade-out
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("frame", [0, WorldCardState.FADE,
                                   WorldCardState.FADE + WorldCardState.HOLD,
                                   WorldCardState.FADE * 2 + WorldCardState.HOLD])
def test_draw_does_not_crash(game, frame):
    card, _ = _make(game)
    card._frame = frame
    surf = pygame.Surface((INTERNAL_W, INTERNAL_H))
    card.draw(surf)


def test_draws_below_is_false():
    assert WorldCardState.draws_below is False
