from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Tuple


@dataclass(frozen=True)
class PlanStep:
    op: str
    args: Dict[str, Any]


@dataclass(frozen=True)
class Expr:
    op: str
    args: Dict[str, Any]


def step(op: str, **kwargs: Any) -> PlanStep:
    return PlanStep(op=op, args=kwargs)


def expr(op: str, **kwargs: Any) -> Expr:
    return Expr(op=op, args=kwargs)


def col(name: str) -> Expr:
    return expr("col", name=name)


def lit(value: Any) -> Expr:
    return expr("lit", value=value)


def param(name: str) -> Expr:
    return expr("param", name=name)


def func(name: str, args: Iterable[Any]) -> Expr:
    return expr("func", name=name, args=tuple(args))


def unary(op: str, value: Any) -> Expr:
    return expr("unary", op=op, value=value)


def binary(op: str, left: Any, right: Any) -> Expr:
    return expr("binary", op=op, left=left, right=right)


def list_(items: Iterable[Any]) -> Expr:
    return expr("list", items=tuple(items))


def map_(items: Iterable[Tuple[str, Any]]) -> Expr:
    return expr("map", items=tuple(items))


def index(base: Any, key: Any) -> Expr:
    return expr("index", base=base, key=key)


def star() -> Expr:
    return expr("star")


def raw(text: str) -> Expr:
    return expr("raw", text=text)


def distinct_expr(value: Any) -> Expr:
    return expr("distinct", value=value)


def plan(*steps: PlanStep) -> Tuple[PlanStep, ...]:
    return steps


def match(*chain: Any) -> PlanStep:
    return step("match", chain=chain)


def rows(table: str, source: Optional[str] = None) -> PlanStep:
    args: Dict[str, Any] = {"table": table}
    if source is not None:
        args["source"] = source
    return step("rows", **args)


def select(items: Iterable[Tuple[str, Any]]) -> PlanStep:
    return step("select", items=tuple(items))


def order_by(keys: Iterable[Tuple[str, Any]]) -> PlanStep:
    return step("order_by", keys=tuple(keys))


def skip(value: Any) -> PlanStep:
    return step("skip", value=value)


def limit(value: Any) -> PlanStep:
    return step("limit", value=value)


def distinct() -> PlanStep:
    return step("distinct")


def group_by(keys: Iterable[Any]) -> PlanStep:
    return step("group_by", keys=tuple(keys))
