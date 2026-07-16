"""Tests for the GameOverState end screen and high-score name entry."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from unittest.mock import patch

import pygame
import pytest

from saruman.config import INTERNAL_H, INTERNAL_W
from saruman.core.state import StateStack
from saruman.states.gameover import GameOverState


class _MockGame:
    def __init__(self) -> None:
        self.states = StateStack()


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
    with patch("saruman.states.gameover.get_audio"):
        yield


@pytest.fixture(autouse=True)
def _isolate_highscores():
    """Keep tests off the real high-score file."""
    with patch("saruman.save.highscores.load", return_value=[]), \
         patch("saruman.save.highscores.save"):
        yield


@pytest.fixture
def game() -> _MockGame:
    return _MockGame()


def _char_event(ch: str) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, key=ord(ch), mod=0, unicode=ch)


def _key_event(key: int, unicode: str = "") -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode=unicode)


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

def test_stores_score(game):
    go = GameOverState(game, score=4321)
    assert go._score == 4321


def test_won_defaults_false(game):
    go = GameOverState(game, score=100)
    assert go._won is False


def test_positive_score_qualifies_when_table_empty(game):
    go = GameOverState(game, score=100)
    assert go._qualify is True


def test_zero_score_does_not_qualify(game):
    go = GameOverState(game, score=0)
    assert go._qualify is False


def test_draws_below_is_false():
    assert GameOverState.draws_below is False


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

def test_on_enter_plays_complete_sfx_when_won(game):
    with patch("saruman.states.gameover.get_audio") as ga:
        go = GameOverState(game, score=100, won=True)
        go.on_enter()
    ga.return_value.play_sfx.assert_called_once_with("level_complete.wav")


def test_on_enter_no_sfx_when_lost(game):
    with patch("saruman.states.gameover.get_audio") as ga:
        go = GameOverState(game, score=100, won=False)
        go.on_enter()
    ga.return_value.play_sfx.assert_not_called()


def test_update_cycles_blink(game):
    go = GameOverState(game, score=100)
    go._blink = 59
    go.update(1 / 60)
    assert go._blink == 0


# ---------------------------------------------------------------------------
# Name entry (qualifying score)
# ---------------------------------------------------------------------------

def test_typing_appends_uppercase(game):
    go = GameOverState(game, score=100)
    go.handle_event(_char_event("a"))
    assert go._name == "A"


def test_backspace_removes_last_char(game):
    go = GameOverState(game, score=100)
    go._name = "AB"
    go.handle_event(_key_event(pygame.K_BACKSPACE))
    assert go._name == "A"


def test_name_capped_at_max(game):
    go = GameOverState(game, score=100)
    go._name = "X" * GameOverState._MAX_NAME
    go.handle_event(_char_event("y"))
    assert go._name == "X" * GameOverState._MAX_NAME


def test_whitespace_char_ignored(game):
    go = GameOverState(game, score=100)
    go.handle_event(_key_event(pygame.K_SPACE, unicode=" "))
    assert go._name == ""


def test_enter_finishes_and_routes_to_highscore(game):
    from saruman.states.highscore import HighScoreState
    go = GameOverState(game, score=100)
    go._name = "ME"
    go.handle_event(_key_event(pygame.K_RETURN, unicode="\r"))
    assert go._done is True
    assert isinstance(game.states.current, HighScoreState)


def test_events_ignored_after_done(game):
    go = GameOverState(game, score=100)
    go._done = True
    go.handle_event(_char_event("a"))
    assert go._name == ""


# ---------------------------------------------------------------------------
# Non-qualifying score: any key advances
# ---------------------------------------------------------------------------

def test_any_key_advances_when_not_qualifying(game):
    from saruman.states.highscore import HighScoreState
    go = GameOverState(game, score=0)
    go.handle_event(_key_event(pygame.K_LEFT))
    assert go._done is True
    assert isinstance(game.states.current, HighScoreState)


# ---------------------------------------------------------------------------
# draw() smoke
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("score,won", [(0, False), (5000, False), (5000, True)])
def test_draw_does_not_crash(game, score, won):
    go = GameOverState(game, score=score, won=won)
    surf = pygame.Surface((INTERNAL_W, INTERNAL_H))
    go.draw(surf)
