from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    handler: Callable[..., dict]
    required_args: tuple[str, ...] = field(default_factory=tuple)
    optional_args: tuple[str, ...] = field(default_factory=tuple)

    def public_schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "required_args": list(self.required_args),
            "optional_args": list(self.optional_args),
        }
