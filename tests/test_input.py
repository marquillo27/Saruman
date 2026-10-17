"""Tests for Input key tracking, including resync after pause / focus loss."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from saruman.core.input import Action, Input
from saruman.core.state import StateStack


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    pygame.display.set_mode((1, 1))
    from saruman.ui import theme
    theme._cache.clear()
    yield
    pygame.quit()


def _keys(*down: int):
    """Fake pygame.key.get_pressed() result with only `down` keys held."""
    class _Pressed:
        def __getitem__(self, key: int) -> bool:
            return key in down
    return lambda: _Pressed()


def _down(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode="")


def test_sync_drops_key_released_elsewhere(monkeypatch):
    inp = Input()
    inp.handle_event(_down(pygame.K_RIGHT))
    assert inp.held(Action.MOVE_RIGHT)
    monkeypatch.setattr(pygame.key, "get_pressed", _keys())
    inp.sync_held()
    assert not inp.held(Action.MOVE_RIGHT)


def test_sync_picks_up_key_pressed_elsewhere(monkeypatch):
    inp = Input()
    monkeypatch.setattr(pygame.key, "get_pressed", _keys(pygame.K_a))
    inp.sync_held()
    assert inp.held(Action.MOVE_LEFT)
    assert not inp.pressed(Action.MOVE_LEFT)   # no phantom "just pressed"


def test_release_all_clears_everything():
    inp = Input()
    inp.handle_event(_down(pygame.K_SPACE))
    inp.release_all()
    assert not inp.held(Action.JUMP)
    assert not inp.pressed(Action.JUMP)


class _MockGame:
    def __init__(self) -> None:
        self.states = StateStack()

    def shake(self, frames: int = 10) -> None:
        pass


def test_resume_from_pause_unsticks_movement(monkeypatch):
    from saruman.states.pause import PauseState
    from saruman.states.play import PlayState

    game = _MockGame()
    play = PlayState(game)
    game.states.push(play)
    play.handle_event(_down(pygame.K_RIGHT))
    assert play._input.held(Action.MOVE_RIGHT)

    play.handle_event(_down(pygame.K_ESCAPE))
    assert isinstance(game.states.current, PauseState)

    # Right arrow released while paused: the KEYUP goes to PauseState only.
    monkeypatch.setattr(pygame.key, "get_pressed", _keys())
    game.states.current.handle_event(_down(pygame.K_ESCAPE))
    assert game.states.current is play
    assert not play._input.held(Action.MOVE_RIGHT)


def test_focus_loss_pauses_and_releases_keys():
    from saruman.states.pause import PauseState
    from saruman.states.play import PlayState

    game = _MockGame()
    play = PlayState(game)
    game.states.push(play)
    play.handle_event(_down(pygame.K_LEFT))
    play.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    assert isinstance(game.states.current, PauseState)
    assert not play._input.held(Action.MOVE_LEFT)
