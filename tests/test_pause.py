"""Tests for the PauseState overlay and its resume / quit-to-menu routing."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from saruman.config import INTERNAL_H, INTERNAL_W
from saruman.core.state import State, StateStack
from saruman.states.pause import PauseState


class _MockGame:
    def __init__(self) -> None:
        self.states = StateStack()


class _SentinelPlay(State):
    """Stand-in for the frozen PlayState beneath the pause overlay."""


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    pygame.display.set_mode((1, 1))
    # A prior module's pygame.quit() invalidates cached Font objects; drop them.
    from saruman.ui import theme
    theme._cache.clear()
    yield
    pygame.quit()


@pytest.fixture
def game() -> _MockGame:
    return _MockGame()


@pytest.fixture
def paused(game) -> PauseState:
    """A pause overlay sitting on top of a sentinel play state."""
    game.states._stack.append(_SentinelPlay())
    ps = PauseState(game)
    game.states._stack.append(ps)
    return ps


def _key_event(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode="")


# ---------------------------------------------------------------------------
# Static config
# ---------------------------------------------------------------------------

def test_draws_below_is_true():
    assert PauseState.draws_below is True


# ---------------------------------------------------------------------------
# Resume (ESC pops only the pause overlay)
# ---------------------------------------------------------------------------

def test_escape_resumes_play(game, paused):
    paused.handle_event(_key_event(pygame.K_ESCAPE))
    assert isinstance(game.states.current, _SentinelPlay)


def test_escape_leaves_play_on_stack(game, paused):
    paused.handle_event(_key_event(pygame.K_ESCAPE))
    assert len(game.states._stack) == 1


# ---------------------------------------------------------------------------
# Quit to menu (ENTER pops pause + play)
# ---------------------------------------------------------------------------

def test_enter_quits_to_empty_stack(game, paused):
    paused.handle_event(_key_event(pygame.K_RETURN))
    assert game.states.is_empty()


@pytest.mark.parametrize("key", [pygame.K_RETURN, pygame.K_SPACE, pygame.K_z])
def test_confirm_keys_quit_to_menu(game, key):
    game.states._stack.append(_SentinelPlay())
    ps = PauseState(game)
    game.states._stack.append(ps)
    ps.handle_event(_key_event(key))
    assert game.states.is_empty()


# ---------------------------------------------------------------------------
# Irrelevant input
# ---------------------------------------------------------------------------

def test_other_key_does_nothing(game, paused):
    paused.handle_event(_key_event(pygame.K_LEFT))
    assert game.states.current is paused


def test_non_keydown_ignored(game, paused):
    paused.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_ESCAPE))
    assert game.states.current is paused


# ---------------------------------------------------------------------------
# draw() smoke
# ---------------------------------------------------------------------------

def test_draw_does_not_crash(paused):
    surf = pygame.Surface((INTERNAL_W, INTERNAL_H))
    paused.draw(surf)
