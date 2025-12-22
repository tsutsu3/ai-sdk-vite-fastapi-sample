from collections.abc import Iterable

from app.features.authz.models import ToolOverrides


def merge_tools(default_tools: Iterable[str] | None, overrides: ToolOverrides | None) -> list[str]:
    overrides = overrides or ToolOverrides()
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
