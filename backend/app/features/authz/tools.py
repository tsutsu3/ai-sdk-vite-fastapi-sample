"""Tool definitions used for authz-driven UI navigation."""

from app.features.authz.models import ToolGroup, ToolItem

TOOL_GROUPS: list[ToolGroup] = [
    ToolGroup(
        id="tool01",
        items=[
            ToolItem(id="tool0101"),
            ToolItem(id="tool0102"),
        ],
    ),
    ToolGroup(
        id="tool02",
        items=[
            ToolItem(id="tool0201"),
            ToolItem(id="tool0202"),
        ],
    ),
    ToolGroup(
        id="tool03",
        items=[
            ToolItem(id="tool0301"),
            ToolItem(id="tool0302"),
        ],
    ),
]
