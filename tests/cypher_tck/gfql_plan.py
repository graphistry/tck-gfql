from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Tuple


@dataclass(frozen=True)
class PlanStep:
    op: str
    args: Dict[str, Any]


def step(op: str, **kwargs: Any) -> PlanStep:
    return PlanStep(op=op, args=kwargs)


def plan(*steps: PlanStep) -> Tuple[PlanStep, ...]:
    return steps


def match(*chain: Any) -> PlanStep:
    return step("match", chain=chain)


def rows(table: str, source: Optional[str] = None) -> PlanStep:
    args: Dict[str, Any] = {"table": table}
    if source is not None:
        args["source"] = source
    return step("rows", **args)


def select(items: Iterable[Tuple[str, str]]) -> PlanStep:
    return step("select", items=tuple(items))


def order_by(keys: Iterable[Tuple[str, str]]) -> PlanStep:
    return step("order_by", keys=tuple(keys))


def skip(value: Any) -> PlanStep:
    return step("skip", value=value)


def limit(value: Any) -> PlanStep:
    return step("limit", value=value)


def distinct() -> PlanStep:
    return step("distinct")


def group_by(keys: Iterable[str]) -> PlanStep:
    return step("group_by", keys=tuple(keys))


def placeholder(note: str, **kwargs: Any) -> PlanStep:
    payload = {"note": note}
    payload.update(kwargs)
    return step("placeholder", **payload)


def is_placeholder(value: Any) -> bool:
    if not isinstance(value, (tuple, list)):
        return False
    for item in value:
        if isinstance(item, PlanStep) and item.op == "placeholder":
            return True
    return False
