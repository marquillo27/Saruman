from __future__ import annotations

import pygame

from saruman.config import TILE_SIZE


def _overlapping_tiles(rect: pygame.Rect, map_w: int, map_h: int):
    left   = max(0, rect.left  // TILE_SIZE)
    right  = min(map_w - 1, (rect.right  - 1) // TILE_SIZE)
    top    = max(0, rect.top   // TILE_SIZE)
    bottom = min(map_h - 1, (rect.bottom - 1) // TILE_SIZE)
    for ty in range(top, bottom + 1):
        for tx in range(left, right + 1):
            yield tx, ty


def move_and_collide(entity, tilemap) -> None:
    """Move entity by velocity, resolve solid-tile collisions (X then Y)."""

    # --- X axis ---
    entity.x += entity.vel_x
    r = entity.rect
    for tx, ty in _overlapping_tiles(r, tilemap.width, tilemap.height):
        if not tilemap.is_solid(tx, ty):
            continue
        tile_rect = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        clip = r.clip(tile_rect)
        if clip.width == 0:
            continue
        # Snap to tile face rather than offsetting by clip width
        if r.centerx < tile_rect.centerx:
            entity.x = float(tile_rect.left - entity.w)
        else:
            entity.x = float(tile_rect.right)
        entity.vel_x = 0.0
        r = entity.rect

    # --- Y axis ---
    entity.y += entity.vel_y
    r = entity.rect
    entity.on_ground = False
    for tx, ty in _overlapping_tiles(r, tilemap.width, tilemap.height):
        if not tilemap.is_solid(tx, ty):
            continue
        tile_rect = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        clip = r.clip(tile_rect)
        if clip.height == 0:
            continue
        if r.centery < tile_rect.centery:
            # Landing on top — snap entity bottom to tile top
            entity.y = float(tile_rect.top - entity.h)
            entity.on_ground = True
        else:
            # Hitting ceiling — snap entity top to tile bottom
            entity.y = float(tile_rect.bottom)
        entity.vel_y = 0.0
        r = entity.rect

    # --- Ground probe (handles the exact-boundary case) ---
    # When resting on a tile, the rect bottom touches the tile top with zero
    # overlap, so the loop above misses it. A 1 px probe catches this.
    if not entity.on_ground:
        probe = pygame.Rect(r.left, r.bottom, r.width, 1)
        for tx, ty in _overlapping_tiles(probe, tilemap.width, tilemap.height):
            if tilemap.is_solid(tx, ty):
                entity.on_ground = True
                if entity.vel_y > 0:
                    entity.vel_y = 0.0
                break


def platform_carry(player, platforms) -> None:
    """One-way collision + carry: treat each MovingPlatform as a top-only solid.

    Called after `move_and_collide(player, tilemap)`. If the player's feet are on
    the platform's top edge (within 2 px) and they are not moving up, snap them
    flush to the platform top, zero their downward velocity, and apply the
    platform's per-frame delta so the player rides it.
    """
    pr = player.rect
    for plat in platforms:
        plr = plat.rect
        # Skip platforms that aren't horizontally overlapping the player
        if pr.right <= plr.left or pr.left >= plr.right:
            continue
        # Player must be near the top face of the platform, not below it
        if player.vel_y < 0:
            continue
        # Player's feet within a small window above the platform top
        if pr.bottom < plr.top - 1 or pr.bottom > plr.top + 4:
            continue
        # Land on the platform
        player.y         = float(plr.top - player.h)
        player.vel_y     = 0.0
        player.on_ground = True
        # Carry horizontally and vertically with the platform's delta
        player.x += plat.delta_x
        player.y += plat.delta_y
        pr = player.rect
