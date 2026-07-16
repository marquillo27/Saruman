"""Tests for the MenuState main-menu navigation and routing."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from unittest.mock import patch

import pygame
import pytest

from saruman.config import INTERNAL_H, INTERNAL_W
from saruman.core.state import StateStack
from saruman.states.menu import MenuState, _ITEMS


class _MockGame:
    def __init__(self) -> None:
        self.states = StateStack()
        self.quit_called = False

    def quit(self) -> None:
        self.quit_called = True


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    pygame.display.set_mode((1, 1))
    # A prior module's pygame.quit() invalidates cached Font objects; drop them.
    from saruman.ui import theme
    theme._cache.clear()
    yield
    pygame.quit()


@pytest.fixture(autouse=True)
def _silence_audio():
    with patch("saruman.states.menu.get_audio"):
        yield


@pytest.fixture
def game() -> _MockGame:
    return _MockGame()


@pytest.fixture
def menu(game) -> MenuState:
    return MenuState(game)


def _key_event(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode="")


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

def test_cursor_starts_zero(menu):
    assert menu._cursor == 0


def test_draws_below_is_false():
    assert MenuState.draws_below is False


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

def test_on_enter_plays_music(game):
    with patch("saruman.states.menu.get_audio") as ga:
        m = MenuState(game)
        m.on_enter()
    ga.return_value.play_music.assert_called_once_with("menu.ogg")


def test_update_advances_tick(menu):
    before = menu._tick
    menu.update(0.5)
    assert menu._tick == pytest.approx(before + 0.5)


# ---------------------------------------------------------------------------
# Cursor navigation (with wrap-around)
# ---------------------------------------------------------------------------

def test_down_advances_cursor(menu):
    menu.handle_event(_key_event(pygame.K_DOWN))
    assert menu._cursor == 1


def test_s_advances_cursor(menu):
    menu.handle_event(_key_event(pygame.K_s))
    assert menu._cursor == 1


def test_up_wraps_to_last(menu):
    menu.handle_event(_key_event(pygame.K_UP))
    assert menu._cursor == len(_ITEMS) - 1


def test_w_wraps_to_last(menu):
    menu.handle_event(_key_event(pygame.K_w))
    assert menu._cursor == len(_ITEMS) - 1


def test_down_wraps_to_zero_from_last(menu):
    menu._cursor = len(_ITEMS) - 1
    menu.handle_event(_key_event(pygame.K_DOWN))
    assert menu._cursor == 0


def test_non_keydown_ignored(menu):
    menu.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_DOWN))
    assert menu._cursor == 0


# ---------------------------------------------------------------------------
# Confirm / routing
# ---------------------------------------------------------------------------

def test_quit_item_calls_game_quit(game, menu):
    menu._cursor = _ITEMS.index("QUIT")
    menu.handle_event(_key_event(pygame.K_RETURN))
    assert game.quit_called is True


def test_high_scores_pushes_state(game, menu):
    from saruman.states.highscore import HighScoreState
    menu._cursor = _ITEMS.index("HIGH SCORES")
    menu.handle_event(_key_event(pygame.K_z))
    assert isinstance(game.states.current, HighScoreState)


def test_controls_pushes_state(game, menu):
    from saruman.states.controls import ControlsState
    menu._cursor = _ITEMS.index("CONTROLS")
    menu.handle_event(_key_event(pygame.K_SPACE))
    assert isinstance(game.states.current, ControlsState)


# ---------------------------------------------------------------------------
# draw() smoke
# ---------------------------------------------------------------------------

def test_draw_does_not_crash(menu):
    surf = pygame.Surface((INTERNAL_W, INTERNAL_H))
    menu.draw(surf)
