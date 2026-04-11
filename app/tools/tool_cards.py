from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.tools.base import BaseTool


ApprovalClass = Literal["explicit_approval"]
ScopeRule = Literal["single_target"]


@dataclass(frozen=True)
class ToolArgument:
    name: str
    kind: Literal["target"]
    required: bool = True
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind,
            "required": self.required,
            "description": self.description,
        }


@dataclass(frozen=True)
class ToolCard:
    key: str
    display_name: str
    summary: str
    approval_class: ApprovalClass
    scope_rule: ScopeRule
    allowed_categories: tuple[str, ...]
    arguments: tuple[ToolArgument, ...]
    artifacts: tuple[str, ...] = ()
    common_followups: tuple[str, ...] = ()
    failure_modes: tuple[str, ...] = ()
    operator_notes: str = ""
    preconditions: tuple[str, ...] = ()
    postconditions: tuple[str, ...] = ()
    safety_notes: tuple[str, ...] = ()
    argument_validation: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "display_name": self.display_name,
            "summary": self.summary,
            "approval_class": self.approval_class,
            "scope_rule": self.scope_rule,
            "allowed_categories": list(self.allowed_categories),
            "arguments": [item.to_dict() for item in self.arguments],
            "artifacts": list(self.artifacts),
            "common_followups": list(self.common_followups),
            "failure_modes": list(self.failure_modes),
            "operator_notes": self.operator_notes,
            "preconditions": list(self.preconditions),
            "postconditions": list(self.postconditions),
            "safety_notes": list(self.safety_notes),
            "argument_validation": list(self.argument_validation),
        }


from typing import Callable, Any

@dataclass(frozen=True)
class ToolRegistration:
    card: ToolCard
    tool: BaseTool
    parser: Callable[[str], dict[str, Any]] | None = None
    stores_findings: bool = False
    generates_report: bool = False
    uses_watcher: bool = False