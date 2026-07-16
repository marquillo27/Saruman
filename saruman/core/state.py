from __future__ import annotations

import pygame


class State:
    draws_below: bool = False

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pass

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass


class StateStack:
    def __init__(self) -> None:
        self._stack: list[State] = []

    @property
    def current(self) -> State | None:
        return self._stack[-1] if self._stack else None

    def push(self, state: State) -> None:
        if self._stack:
            self._stack[-1].on_exit()
        self._stack.append(state)
        state.on_enter()

    def pop(self) -> State | None:
        if not self._stack:
            return None
        state = self._stack.pop()
        state.on_exit()
        if self._stack:
            self._stack[-1].on_enter()
        return state

    def replace(self, state: State) -> None:
        if self._stack:
            self._stack.pop().on_exit()
        self._stack.append(state)
        state.on_enter()

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.current:
            self.current.handle_event(event)

    def update(self, dt: float) -> None:
        if self.current:
            self.current.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        visible: list[State] = []
        for state in reversed(self._stack):
            visible.append(state)
            if not state.draws_below:
                break
        for state in reversed(visible):
            state.draw(surface)

    def is_empty(self) -> bool:
        return not self._stack
