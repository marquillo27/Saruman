"""Shared TMX serialization helpers for the level_07..10 generator scripts.

Extracted to remove the identical _obj_xml/_grid_to_csv/_build_tmx copies that
lived in each generator. Output is byte-identical to the previous inline code.
"""
from __future__ import annotations


def grid_to_csv(grid: list[list[int]]) -> str:
    """Tiled CSV with trailing comma per row + newline; pytmx-tolerant."""
    return "\n".join(",".join(str(v) for v in row) + "," for row in grid)[:-1]


def obj_xml(obj: dict, indent: str = "  ") -> str:
    """Serialize one object dict (keys: id, type, x, y, w, h, props) to a TMX
    <object> element."""
    x, y, w, h = obj["x"], obj["y"], obj["w"], obj["h"]
    props = obj.get("props", {})

    tag = (f'{indent}<object id="{obj["id"]}"  type="{obj["type"]}"'
           f' x="{x}" y="{y}" width="{w}" height="{h}"')
    if not props:
        return tag + "/>"

    lines = [tag + ">", f"{indent} <properties>"]
    for k, v in props.items():
        vtype = "int" if isinstance(v, int) else "string"
        lines.append(f'{indent}  <property name="{k}" type="{vtype}" value="{v}"/>')
    lines.append(f"{indent} </properties>")
    lines.append(f"{indent}</object>")
    return "\n".join(lines)


def build_tmx(
    grid: list[list[int]], objs: list[dict], width: int, height: int, tile: int,
) -> str:
    """Assemble a full orthogonal TMX document from a tile grid and object list."""
    csv = grid_to_csv(grid)
    objs_xml = "\n".join(obj_xml(o) for o in objs)
    next_oid = max(o["id"] for o in objs) + 1

    return f"""\
<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="orthogonal"
     renderorder="right-down" width="{width}" height="{height}"
     tilewidth="{tile}" tileheight="{tile}" infinite="0"
     nextlayerid="3" nextobjectid="{next_oid}">
 <tileset firstgid="1" name="kenney_platformer" tilewidth="{tile}" tileheight="{tile}"
          tilecount="132" columns="12">
  <image source="../tilesets/tilemap_packed.png" width="192" height="176"/>
 </tileset>
 <layer id="1" name="solid" width="{width}" height="{height}">
  <data encoding="csv">
{csv}
  </data>
 </layer>
 <objectgroup id="2" name="entities">
{objs_xml}
 </objectgroup>
</map>
"""
