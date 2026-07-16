from __future__ import annotations

from enum import auto, Enum

import pygame


class Action(Enum):
    MOVE_LEFT  = auto()
    MOVE_RIGHT = auto()
    JUMP       = auto()
    SHOOT      = auto()
    SWING      = auto()
    SHIELD     = auto()
    PAUSE      = auto()


_KEYMAP: dict[int, Action] = {
    pygame.K_LEFT:   Action.MOVE_LEFT,
    pygame.K_a:      Action.MOVE_LEFT,
    pygame.K_RIGHT:  Action.MOVE_RIGHT,
    pygame.K_d:      Action.MOVE_RIGHT,
    pygame.K_SPACE:  Action.JUMP,
    pygame.K_UP:     Action.JUMP,
    pygame.K_w:      Action.JUMP,
    pygame.K_z:      Action.JUMP,
    pygame.K_j:      Action.SHOOT,
    pygame.K_x:      Action.SHOOT,
    pygame.K_k:      Action.SWING,
    pygame.K_c:      Action.SWING,
    pygame.K_l:      Action.SHIELD,
    pygame.K_q:      Action.SHIELD,
    pygame.K_ESCAPE: Action.PAUSE,
}


class Input:
    def __init__(self) -> None:
        self._held:     set[Action] = set()
        self._pressed:  set[Action] = set()
        self._released: set[Action] = set()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            action = _KEYMAP.get(event.key)
            if action:
                self._held.add(action)
                self._pressed.add(action)
        elif event.type == pygame.KEYUP:
            action = _KEYMAP.get(event.key)
            if action:
                self._held.discard(action)
                self._released.add(action)

    def clear_frame(self) -> None:
        self._pressed.clear()
        self._released.clear()

    def held(self, action: Action) -> bool:
        return action in self._held

    def pressed(self, action: Action) -> bool:
        return action in self._pressed

    def released(self, action: Action) -> bool:
        return action in self._released
