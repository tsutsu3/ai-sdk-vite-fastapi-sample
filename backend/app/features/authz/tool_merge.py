from collections.abc import Iterable

from app.features.authz.models import ToolOverridesRecord


def merge_tools(
    default_tool_ids: Iterable[str] | None,
    overrides: ToolOverridesRecord | None,
    *,
    available_tool_ids: set[str] | None = None,
) -> list[str]:
    """Merge default tool ids with allow/deny overrides."""
    overrides = overrides or ToolOverridesRecord()
    allow = list(overrides.allow or [])
    deny = {tool.strip() for tool in overrides.deny if tool and tool.strip()}
    available = available_tool_ids or set()

    result: list[str] = []
    seen: set[str] = set()
    for tool_id in list(default_tool_ids or []) + allow:
        normalized = (tool_id or "").strip()
        if not normalized or normalized in deny:
            continue
        if available and normalized not in available:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)

    if deny:
        result = [tool_id for tool_id in result if tool_id not in deny]

    return result
