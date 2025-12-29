from collections.abc import Iterable

from app.features.authz.models import ToolOverridesRecord


def merge_tools(
    default_tools: Iterable[str] | None, overrides: ToolOverridesRecord | None
) -> list[str]:
    """Merge default tools with allow/deny overrides.

    Args:
        default_tools: Default tool identifiers.
        overrides: Tool overrides with allow/deny lists.

    Returns:
        list[str]: Final tool list without duplicates.
    """
    overrides = overrides or ToolOverridesRecord()
    allow = overrides.allow
    deny = set(overrides.deny)

    result: list[str] = []
    seen: set[str] = set()
    for tool in list(default_tools or []) + allow:
        if tool in deny or tool in seen:
            continue
        seen.add(tool)
        result.append(tool)
    return result
