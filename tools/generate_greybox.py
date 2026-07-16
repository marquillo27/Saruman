"""
One-time script — generates greybox placeholder assets.
Run from project root:  uv run python tools/generate_greybox.py

If assets/tilesets/tilemap_packed.png (Kenney Pixel Platformer, CC0) is
present, the TMX files reference that tileset with grass-top/stone tile IDs.
Otherwise, the single-tile greybox tileset is used as before.
"""
from __future__ import annotations

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

TILE = 16


# ---------------------------------------------------------------------------
# Tileset: a single 16×16 gray tile (greybox.png)
# ---------------------------------------------------------------------------

def make_tileset() -> pygame.Surface:
    surf = pygame.Surface((TILE, TILE))
    surf.fill((78, 83, 100))
    pygame.draw.rect(surf, (50, 55, 70), (0, 0, TILE, TILE), 1)
    return surf


# ---------------------------------------------------------------------------
# Level 02 — Wolfwood greybox (60 × 12 tiles)
# ---------------------------------------------------------------------------
#
#  Row  6: platform D  (cols 32-36)
#  Row  7: platform B  (cols 14-18)   platform E (cols 43-47)
#  Row  8: platform A  (cols  5-8)    platform C (cols 23-26)
#  Row 11: solid ground
#
#  Objects:
#    PlayerSpawn (32, 160), Goblinkin ×2, Wraith ×1
#    Coins ×3, Heart, WeaponUpgrade
#    Warp (cracked-statue) -> level_03_glass_caverns
#    BossWarg near the end
#    LevelEnd at far right

def build_wolfwood_csv(tile_ground: int, tile_platform: int) -> str:
    W, H = 60, 12
    grid = [[0] * W for _ in range(H)]

    for c in range(W):      grid[11][c] = tile_ground    # ground row
    for c in range(5,  9):  grid[8][c]  = tile_platform  # A
    for c in range(14, 19): grid[7][c]  = tile_platform  # B
    for c in range(23, 27): grid[8][c]  = tile_platform  # C
    for c in range(32, 37): grid[6][c]  = tile_platform  # D
    for c in range(43, 48): grid[7][c]  = tile_platform  # E

    return ",".join(str(g) for row in grid for g in row)


def build_wolfwood_tmx(
    csv: str,
    tileset_src: str,
    tileset_name: str,
    tilecount: int,
    columns: int,
    img_w: int,
    img_h: int,
) -> str:
    return f"""\
<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="orthogonal"
     renderorder="right-down" width="60" height="12"
     tilewidth="16" tileheight="16" infinite="0"
     nextlayerid="3" nextobjectid="20">
 <tileset firstgid="1" name="{tileset_name}" tilewidth="16" tileheight="16"
          tilecount="{tilecount}" columns="{columns}">
  <image source="{tileset_src}" width="{img_w}" height="{img_h}"/>
 </tileset>
 <layer id="1" name="solid" width="60" height="12">
  <data encoding="csv">
{csv}
  </data>
 </layer>
 <objectgroup id="2" name="entities">
  <object id="1"  type="PlayerSpawn"   x="32"   y="160" width="16" height="16"/>
  <object id="2"  type="Goblinkin"     x="100"  y="114" width="12" height="14"/>
  <object id="3"  type="Goblinkin"     x="540"  y="82"  width="12" height="14"/>
  <object id="4"  type="Wraith"        x="380"  y="60"  width="80" height="16"/>
  <object id="5"  type="Coin"          x="64"   y="152" width="8"  height="8"/>
  <object id="6"  type="Coin"          x="96"   y="110" width="8"  height="8"/>
  <object id="7"  type="Coin"          x="240"  y="93"  width="8"  height="8"/>
  <object id="8"  type="Heart"         x="536"  y="78"  width="9"  height="9"/>
  <object id="9"  type="WeaponUpgrade" x="700"  y="94"  width="10" height="10"/>
  <object id="10" type="Warp"          x="416"  y="96"  width="16" height="32">
   <properties>
    <property name="target" value="level_03_glass_caverns"/>
   </properties>
  </object>
  <object id="11" type="BossWarg"      x="832"  y="155" width="24" height="20"/>
  <object id="12" type="LevelEnd"      x="928"  y="144" width="16" height="32">
   <properties>
    <property name="score_bonus" type="int" value="1000"/>
   </properties>
  </object>
 </objectgroup>
</map>
"""


# ---------------------------------------------------------------------------
# Level 03 — Glass Caverns greybox (40 × 12 tiles)
# ---------------------------------------------------------------------------
#
#  Row  0: ceiling (solid, feels underground)
#  Row  2: ledge A  (cols 3-6)
#  Row  4: ledge B  (cols 12-16)
#  Row  6: ledge C  (cols 24-28)
#  Row  8: ledge D  (cols 32-35)
#  Row 11: ground

def build_caverns_csv(tile_ground: int, tile_platform: int) -> str:
    W, H = 40, 12
    grid = [[0] * W for _ in range(H)]

    for c in range(W):      grid[11][c] = tile_ground    # ground
    for c in range(W):      grid[0][c]  = tile_platform  # ceiling (stone)
    for c in range(3,  7):  grid[2][c]  = tile_platform  # ledge A
    for c in range(12, 17): grid[4][c]  = tile_platform  # ledge B
    for c in range(24, 29): grid[6][c]  = tile_platform  # ledge C
    for c in range(32, 36): grid[8][c]  = tile_platform  # ledge D

    return ",".join(str(g) for row in grid for g in row)


def build_caverns_tmx(
    csv: str,
    tileset_src: str,
    tileset_name: str,
    tilecount: int,
    columns: int,
    img_w: int,
    img_h: int,
) -> str:
    return f"""\
<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="orthogonal"
     renderorder="right-down" width="40" height="12"
     tilewidth="16" tileheight="16" infinite="0"
     nextlayerid="3" nextobjectid="15">
 <tileset firstgid="1" name="{tileset_name}" tilewidth="16" tileheight="16"
          tilecount="{tilecount}" columns="{columns}">
  <image source="{tileset_src}" width="{img_w}" height="{img_h}"/>
 </tileset>
 <layer id="1" name="solid" width="40" height="12">
  <data encoding="csv">
{csv}
  </data>
 </layer>
 <objectgroup id="2" name="entities">
  <object id="1"  type="PlayerSpawn"   x="32"   y="160" width="16" height="16"/>
  <object id="2"  type="Goblinkin"     x="80"   y="160" width="12" height="14"/>
  <object id="3"  type="Wraith"        x="200"  y="48"  width="60" height="16"/>
  <object id="4"  type="Goblinkin"     x="392"  y="82"  width="12" height="14"/>
  <object id="5"  type="Coin"          x="64"   y="152" width="8"  height="8"/>
  <object id="6"  type="Coin"          x="200"  y="48"  width="8"  height="8"/>
  <object id="7"  type="Coin"          x="390"  y="80"  width="8"  height="8"/>
  <object id="8"  type="Heart"         x="310"  y="80"  width="9"  height="9"/>
  <object id="9"  type="Coin"          x="136"  y="48"  width="8"  height="8"/>
  <object id="10" type="Coin"          x="256"  y="80"  width="8"  height="8"/>
  <object id="11" type="LevelEnd"      x="592"  y="144" width="16" height="32">
   <properties>
    <property name="score_bonus" type="int" value="2000"/>
   </properties>
  </object>
 </objectgroup>
</map>
"""


# ---------------------------------------------------------------------------
# Level 01 — Greenshire Hills (80 × 12 tiles)  — tutorial
# ---------------------------------------------------------------------------
#
#  Row  7: platform A  (cols  8-13)    Row  6: platform B  (cols 22-28)
#  Row  8: platform C  (cols 36-42)    Row  6: platform D  (cols 52-58)
#  Row  7: platform E  (cols 68-73)    Row 11: solid ground

def build_greenshire_csv(tile_ground: int, tile_platform: int) -> str:
    W, H = 80, 12
    grid = [[0] * W for _ in range(H)]

    for c in range(W):       grid[11][c] = tile_ground    # ground
    for c in range(8,  14):  grid[7][c]  = tile_platform  # A
    for c in range(22, 29):  grid[6][c]  = tile_platform  # B
    for c in range(36, 43):  grid[8][c]  = tile_platform  # C
    for c in range(52, 59):  grid[6][c]  = tile_platform  # D
    for c in range(68, 74):  grid[7][c]  = tile_platform  # E

    return ",".join(str(g) for row in grid for g in row)


def build_greenshire_tmx(
    csv: str, tileset_src: str, tileset_name: str,
    tilecount: int, columns: int, img_w: int, img_h: int,
) -> str:
    return f"""\
<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="orthogonal"
     renderorder="right-down" width="80" height="12"
     tilewidth="16" tileheight="16" infinite="0"
     nextlayerid="3" nextobjectid="20">
 <tileset firstgid="1" name="{tileset_name}" tilewidth="16" tileheight="16"
          tilecount="{tilecount}" columns="{columns}">
  <image source="{tileset_src}" width="{img_w}" height="{img_h}"/>
 </tileset>
 <layer id="1" name="solid" width="80" height="12">
  <data encoding="csv">
{csv}
  </data>
 </layer>
 <objectgroup id="2" name="entities">
  <object id="1"  type="PlayerSpawn"   x="48"   y="144" width="16" height="16"/>
  <object id="2"  type="Goblinkin"     x="192"  y="162" width="12" height="14"/>
  <object id="3"  type="Goblinkin"     x="448"  y="162" width="12" height="14"/>
  <object id="4"  type="Goblinkin"     x="688"  y="162" width="12" height="14"/>
  <object id="5"  type="Coin"          x="144"  y="96"  width="8"  height="8"/>
  <object id="6"  type="Coin"          x="368"  y="80"  width="8"  height="8"/>
  <object id="7"  type="Coin"          x="576"  y="112" width="8"  height="8"/>
  <object id="8"  type="Coin"          x="816"  y="80"  width="8"  height="8"/>
  <object id="9"  type="Coin"          x="1088" y="96"  width="8"  height="8"/>
  <object id="10" type="Coin"          x="64"   y="152" width="8"  height="8"/>
  <object id="11" type="Heart"         x="288"  y="144" width="9"  height="9"/>
  <object id="12" type="WeaponUpgrade" x="640"  y="80"  width="10" height="10"/>
  <object id="13" type="LevelEnd"      x="1216" y="144" width="16" height="32">
   <properties>
    <property name="score_bonus" type="int" value="500"/>
   </properties>
  </object>
 </objectgroup>
</map>
"""


# ---------------------------------------------------------------------------
# Level 04 — Sunken Mines (75 × 12 tiles)
# ---------------------------------------------------------------------------
#
#  Row  0: ceiling (solid)         Row  4: ledge A (cols  5-10)
#  Row  6: ledge B  (cols 18-24)   Row  3: ledge C (cols 33-38)
#  Row  7: ledge D  (cols 48-54)   Row  4: ledge E (cols 62-68)
#  Row 11: ground

def build_mines_csv(tile_ground: int, tile_platform: int) -> str:
    W, H = 75, 12
    grid = [[0] * W for _ in range(H)]

    for c in range(W):       grid[11][c] = tile_ground    # ground
    for c in range(W):       grid[0][c]  = tile_platform  # ceiling
    for c in range(5,  11):  grid[4][c]  = tile_platform  # ledge A
    for c in range(18, 25):  grid[6][c]  = tile_platform  # ledge B
    for c in range(33, 39):  grid[3][c]  = tile_platform  # ledge C
    for c in range(48, 55):  grid[7][c]  = tile_platform  # ledge D
    for c in range(62, 69):  grid[4][c]  = tile_platform  # ledge E

    return ",".join(str(g) for row in grid for g in row)


def build_mines_tmx(
    csv: str, tileset_src: str, tileset_name: str,
    tilecount: int, columns: int, img_w: int, img_h: int,
) -> str:
    return f"""\
<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="orthogonal"
     renderorder="right-down" width="75" height="12"
     tilewidth="16" tileheight="16" infinite="0"
     nextlayerid="3" nextobjectid="20">
 <tileset firstgid="1" name="{tileset_name}" tilewidth="16" tileheight="16"
          tilecount="{tilecount}" columns="{columns}">
  <image source="{tileset_src}" width="{img_w}" height="{img_h}"/>
 </tileset>
 <layer id="1" name="solid" width="75" height="12">
  <data encoding="csv">
{csv}
  </data>
 </layer>
 <objectgroup id="2" name="entities">
  <object id="1"  type="PlayerSpawn"   x="32"   y="144" width="16" height="16"/>
  <object id="2"  type="Goblinkin"     x="192"  y="162" width="12" height="14"/>
  <object id="3"  type="Goblinkin"     x="400"  y="162" width="12" height="14"/>
  <object id="4"  type="Goblinkin"     x="640"  y="162" width="12" height="14"/>
  <object id="5"  type="ShieldKnight"  x="112"  y="48"  width="12" height="16"/>
  <object id="6"  type="ShieldKnight"  x="544"  y="32"  width="12" height="16"/>
  <object id="7"  type="Wraith"        x="288"  y="60"  width="60" height="16"/>
  <object id="8"  type="Coin"          x="128"  y="44"  width="8"  height="8"/>
  <object id="9"  type="Coin"          x="304"  y="76"  width="8"  height="8"/>
  <object id="10" type="Coin"          x="560"  y="26"  width="8"  height="8"/>
  <object id="11" type="Coin"          x="784"  y="92"  width="8"  height="8"/>
  <object id="12" type="Coin"          x="1008" y="44"  width="8"  height="8"/>
  <object id="13" type="Heart"         x="672"  y="100" width="9"  height="9"/>
  <object id="14" type="BossWarg"      x="1104" y="155" width="24" height="20"/>
  <object id="15" type="LevelEnd"      x="1152" y="144" width="16" height="32">
   <properties>
    <property name="score_bonus" type="int" value="1500"/>
   </properties>
  </object>
 </objectgroup>
</map>
"""


# ---------------------------------------------------------------------------
# Level 05 — Ash Marshes (90 × 12 tiles)
# ---------------------------------------------------------------------------
#
#  Row  7: platform A (cols 10-15)    Row  5: platform B (cols 24-30)
#  Row  8: platform C (cols 40-46)    Row  5: platform D (cols 55-61)
#  Row  7: platform E (cols 70-76)    Row  4: platform F (cols 82-87)
#  Row 11: ground

def build_marshes_csv(tile_ground: int, tile_platform: int) -> str:
    W, H = 90, 12
    grid = [[0] * W for _ in range(H)]

    for c in range(W):       grid[11][c] = tile_ground    # ground
    for c in range(10, 16):  grid[7][c]  = tile_platform  # A
    for c in range(24, 31):  grid[5][c]  = tile_platform  # B
    for c in range(40, 47):  grid[8][c]  = tile_platform  # C
    for c in range(55, 62):  grid[5][c]  = tile_platform  # D
    for c in range(70, 77):  grid[7][c]  = tile_platform  # E
    for c in range(82, 88):  grid[4][c]  = tile_platform  # F

    return ",".join(str(g) for row in grid for g in row)


def build_marshes_tmx(
    csv: str, tileset_src: str, tileset_name: str,
    tilecount: int, columns: int, img_w: int, img_h: int,
) -> str:
    return f"""\
<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="orthogonal"
     renderorder="right-down" width="90" height="12"
     tilewidth="16" tileheight="16" infinite="0"
     nextlayerid="3" nextobjectid="22">
 <tileset firstgid="1" name="{tileset_name}" tilewidth="16" tileheight="16"
          tilecount="{tilecount}" columns="{columns}">
  <image source="{tileset_src}" width="{img_w}" height="{img_h}"/>
 </tileset>
 <layer id="1" name="solid" width="90" height="12">
  <data encoding="csv">
{csv}
  </data>
 </layer>
 <objectgroup id="2" name="entities">
  <object id="1"  type="PlayerSpawn"   x="32"   y="144" width="16" height="16"/>
  <object id="2"  type="Goblinkin"     x="160"  y="162" width="12" height="14"/>
  <object id="3"  type="Goblinkin"     x="496"  y="162" width="12" height="14"/>
  <object id="4"  type="Goblinkin"     x="800"  y="162" width="12" height="14"/>
  <object id="5"  type="Goblinkin"     x="1072" y="162" width="12" height="14"/>
  <object id="6"  type="ShieldKnight"  x="384"  y="66"  width="12" height="16"/>
  <object id="7"  type="ShieldKnight"  x="880"  y="66"  width="12" height="16"/>
  <object id="8"  type="Wraith"        x="240"  y="50"  width="50" height="16"/>
  <object id="9"  type="Wraith"        x="700"  y="50"  width="50" height="16"/>
  <object id="10" type="Coin"          x="176"  y="96"  width="8"  height="8"/>
  <object id="11" type="Coin"          x="400"  y="64"  width="8"  height="8"/>
  <object id="12" type="Coin"          x="640"  y="112" width="8"  height="8"/>
  <object id="13" type="Coin"          x="880"  y="64"  width="8"  height="8"/>
  <object id="14" type="Coin"          x="1120" y="96"  width="8"  height="8"/>
  <object id="15" type="Heart"         x="560"  y="152" width="9"  height="9"/>
  <object id="16" type="WeaponUpgrade" x="1312" y="48"  width="10" height="10"/>
  <object id="17" type="LevelEnd"      x="1376" y="144" width="16" height="32">
   <properties>
    <property name="score_bonus" type="int" value="2500"/>
   </properties>
  </object>
 </objectgroup>
</map>
"""


# ---------------------------------------------------------------------------
# Level 06 — Pale Tower (65 × 12 tiles)  — final
# ---------------------------------------------------------------------------
#
#  Row  9: platform A (cols  3-6)     Row  7: platform B (cols  9-13)
#  Row  5: platform C (cols 16-20)    Row  7: platform D (cols 24-29)
#  Row  4: platform E (cols 33-37)    Row  2: platform F (cols 41-45)
#  Row  5: platform G (cols 50-54)    Row  7: platform H (cols 58-62)
#  Row 11: ground

def build_tower_csv(tile_ground: int, tile_platform: int) -> str:
    W, H = 65, 12
    grid = [[0] * W for _ in range(H)]

    for c in range(W):       grid[11][c] = tile_ground    # ground
    for c in range(3,  7):   grid[9][c]  = tile_platform  # A
    for c in range(9,  14):  grid[7][c]  = tile_platform  # B
    for c in range(16, 21):  grid[5][c]  = tile_platform  # C
    for c in range(24, 30):  grid[7][c]  = tile_platform  # D
    for c in range(33, 38):  grid[4][c]  = tile_platform  # E
    for c in range(41, 46):  grid[2][c]  = tile_platform  # F
    for c in range(50, 55):  grid[5][c]  = tile_platform  # G
    for c in range(58, 63):  grid[7][c]  = tile_platform  # H

    return ",".join(str(g) for row in grid for g in row)


def build_tower_tmx(
    csv: str, tileset_src: str, tileset_name: str,
    tilecount: int, columns: int, img_w: int, img_h: int,
) -> str:
    return f"""\
<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="orthogonal"
     renderorder="right-down" width="65" height="12"
     tilewidth="16" tileheight="16" infinite="0"
     nextlayerid="3" nextobjectid="22">
 <tileset firstgid="1" name="{tileset_name}" tilewidth="16" tileheight="16"
          tilecount="{tilecount}" columns="{columns}">
  <image source="{tileset_src}" width="{img_w}" height="{img_h}"/>
 </tileset>
 <layer id="1" name="solid" width="65" height="12">
  <data encoding="csv">
{csv}
  </data>
 </layer>
 <objectgroup id="2" name="entities">
  <object id="1"  type="PlayerSpawn"   x="32"   y="144" width="16" height="16"/>
  <object id="2"  type="Goblinkin"     x="64"   y="130" width="12" height="14"/>
  <object id="3"  type="Goblinkin"     x="384"  y="98"  width="12" height="14"/>
  <object id="4"  type="ShieldKnight"  x="160"  y="66"  width="12" height="16"/>
  <object id="5"  type="ShieldKnight"  x="528"  y="66"  width="12" height="16"/>
  <object id="6"  type="ShieldKnight"  x="656"  y="98"  width="12" height="16"/>
  <object id="7"  type="Wraith"        x="256"  y="50"  width="50" height="16"/>
  <object id="8"  type="Wraith"        x="720"  y="82"  width="50" height="16"/>
  <object id="9"  type="Coin"          x="80"   y="120" width="8"  height="8"/>
  <object id="10" type="Coin"          x="176"  y="64"  width="8"  height="8"/>
  <object id="11" type="Coin"          x="384"  y="48"  width="8"  height="8"/>
  <object id="12" type="Coin"          x="672"  y="16"  width="8"  height="8"/>
  <object id="13" type="Coin"          x="800"  y="64"  width="8"  height="8"/>
  <object id="14" type="Coin"          x="944"  y="96"  width="8"  height="8"/>
  <object id="15" type="Heart"         x="256"  y="112" width="9"  height="9"/>
  <object id="16" type="Heart"         x="640"  y="50"  width="9"  height="9"/>
  <object id="17" type="BossWarg"      x="896"  y="155" width="24" height="20"/>
  <object id="18" type="BossWarg"      x="960"  y="155" width="24" height="20"/>
  <object id="19" type="LevelEnd"      x="1008" y="144" width="16" height="32">
   <properties>
    <property name="score_bonus" type="int" value="5000"/>
   </properties>
  </object>
 </objectgroup>
</map>
"""


# ---------------------------------------------------------------------------
# Write files
# ---------------------------------------------------------------------------

def main() -> None:
    kenney_png = os.path.join(ROOT, "assets", "tilesets", "tilemap_packed.png")

    if os.path.exists(kenney_png):
        tileset_src  = "../tilesets/tilemap_packed.png"
        tileset_name = "kenney_platformer"
        tilecount, columns, img_w, img_h = 132, 12, 192, 176
        tile_ground   = 1   # grass-top  (col 0, row 0 of tilemap_packed)
        tile_platform = 3   # stone slab (col 2, row 0 of tilemap_packed)
        print("  Kenney tileset detected — using Kenney tile IDs.")
    else:
        tileset_src  = "../tilesets/greybox.png"
        tileset_name = "greybox"
        tilecount, columns, img_w, img_h = 1, 1, 16, 16
        tile_ground = tile_platform = 1
        print("  Kenney tileset not found — using greybox fallback.")

    maps_dir     = os.path.join(ROOT, "assets", "maps")
    tileset_path = os.path.join(ROOT, "assets", "tilesets", "greybox.png")

    pygame.image.save(make_tileset(), tileset_path)
    print(f"  greybox.png: {tileset_path}")

    levels = [
        ("level_01_greenshire_hills", build_greenshire_csv, build_greenshire_tmx),
        ("level_02_wolfwood",         build_wolfwood_csv,   build_wolfwood_tmx),
        ("level_03_glass_caverns",    build_caverns_csv,    build_caverns_tmx),
        ("level_04_sunken_mines",     build_mines_csv,      build_mines_tmx),
        ("level_05_ash_marshes",      build_marshes_csv,    build_marshes_tmx),
        ("level_06_pale_tower",       build_tower_csv,      build_tower_tmx),
    ]

    kwargs = dict(
        tileset_src=tileset_src, tileset_name=tileset_name,
        tilecount=tilecount, columns=columns, img_w=img_w, img_h=img_h,
    )

    for stem, csv_fn, tmx_fn in levels:
        path = os.path.join(maps_dir, f"{stem}.tmx")
        with open(path, "w", encoding="utf-8") as f:
            f.write(tmx_fn(csv_fn(tile_ground, tile_platform), **kwargs))
        print(f"  {stem}.tmx")

    pygame.quit()
    print(f"Done — {len(levels)} levels written.")


if __name__ == "__main__":
    main()
