"""Tool definitions used for authz-driven UI navigation."""

from collections import defaultdict

from app.features.authz.models import ToolGroup, ToolItem
from app.features.tool_catalog.models import ToolRecord


def build_tool_groups(tools: list[ToolRecord], allowed_tool_ids: list[str]) -> list[ToolGroup]:
    """Build tool groups for UI from allowed tool records."""
    allowed = {tool_id for tool_id in allowed_tool_ids if tool_id}
    grouped: dict[str, list[str]] = defaultdict(list)
    group_order: dict[str, int] = {}

    for tool in tools:
        if not tool.enabled or tool.id not in allowed:
            continue
        grouped[tool.group_id].append(tool.id)
        if tool.group_order is not None:
            group_order.setdefault(tool.group_id, tool.group_order)

    groups: list[ToolGroup] = []
    for group_id, tool_ids in grouped.items():
        items = [ToolItem(id=tool_id) for tool_id in tool_ids]
        groups.append(ToolGroup(id=group_id, items=items))

    return sorted(groups, key=lambda group: group_order.get(group.id, 0))
