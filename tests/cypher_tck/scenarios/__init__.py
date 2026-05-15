from __future__ import annotations

from dataclasses import dataclass, replace
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re
from typing import Iterable, Optional, Tuple

from tests.cypher_tck.direct_cypher_support import (
    DIRECT_CYPHER_PROMOTION_ERROR_KEYS,
    DIRECT_CYPHER_PROMOTION_ROW_KEYS,
)
from tests.cypher_tck.gfql_plan import (
    PlanStep,
    binary,
    col,
    distinct,
    distinct_expr,
    func,
    index,
    limit,
    list_,
    lit,
    map_,
    order_by,
    param,
    plan,
    raw,
    select,
    skip,
    star,
    step,
    unary,
)
from tests.cypher_tck.models import Scenario
from tests.cypher_tck.phase_support import (
    PHASE1_CYPHER_STRING_PURE_KEYS,
    PHASE1_EXECUTOR_PURE_ERROR_KEYS,
    PHASE1_EXECUTOR_PURE_KEYS,
    PHASE1_EXECUTOR_SUPPORTED_ERROR_KEYS,
    PHASE1_EXECUTOR_SUPPORTED_KEYS,
)

_SCENARIO_ROOT = Path(__file__).resolve().parent / "tck" / "features"
SCENARIOS: list[Scenario] = []

_TARGET_TABLE_PREFIXES = (
    "clauses/return",
    "clauses/with",
)

_TARGET_EXPR_PREFIXES = (
    "expressions/aggregation",
    "expressions/boolean",
    "expressions/comparison",
    "expressions/list",
    "expressions/literals",
    "expressions/map",
    "expressions/mathematical",
    "expressions/null",
    "expressions/precedence",
    "expressions/quantifier",
    "expressions/string",
    "expressions/temporal",
    "expressions/typeConversion",
)

_DEFER_EXPR_PREFIXES = (
    "expressions/conditional",
    "expressions/existentialSubqueries",
    "expressions/graph",
    "expressions/pattern",
)


def _merge_tags(existing: Tuple[str, ...], extra: Iterable[str]) -> Tuple[str, ...]:
    tags = list(existing)
    for tag in extra:
        if tag not in tags:
            tags.append(tag)
    return tuple(tags)


def _extension_tags(feature_path: str) -> Tuple[str, ...]:
    tags = []
    if any(prefix in feature_path for prefix in _TARGET_TABLE_PREFIXES):
        tags.append("target-table-ops")
    if any(prefix in feature_path for prefix in _TARGET_EXPR_PREFIXES):
        tags.append("target-expr-dsl")
    if "expressions/quantifier" in feature_path:
        tags.append("defer-quantifier")
    if "expressions/path" in feature_path:
        tags.append("defer-path-enum")
    if any(prefix in feature_path for prefix in _DEFER_EXPR_PREFIXES):
        tags.append("defer-expr-advanced")
    if "clauses/unwind" in feature_path:
        tags.append("defer-unwind")
    if "clauses/union" in feature_path:
        tags.append("defer-union")
    return tuple(tags)


def _tag_scenario(scenario: Scenario) -> Scenario:
    if scenario.status != "xfail":
        return scenario
    extra_tags = _extension_tags(scenario.feature_path)
    if not extra_tags:
        return scenario
    return replace(scenario, tags=_merge_tags(scenario.tags, extra_tags))


_CLAUSE_RE = re.compile(
    r"(?im)(?:^\s*(OPTIONAL MATCH|ORDER BY|MATCH|WHERE|WITH|RETURN|UNWIND|SKIP|LIMIT|CREATE|MERGE|DELETE|SET|REMOVE|CALL)\b)"
    r"|(?:\s(SKIP|LIMIT)\b)"
)
_ORDER_DIR_RE = re.compile(r"(?is)^(?P<expr>.+?)\s+(?P<dir>asc(?:ending)?|desc(?:ending)?)$")
_WITH_ORDERBY_KEY_RE = re.compile(
    r"^with-orderby(?P<feature>\d+)-(?P<scenario>\d+)(?:-\d+)?$"
)

_WITH_ORDERBY_ORDERED_SCENARIO_NUMBERS = {
    "WithOrderBy1.feature": frozenset(range(1, 21)),
    "WithOrderBy2.feature": frozenset(),
    "WithOrderBy3.feature": frozenset(),
    "WithOrderBy4.feature": frozenset({15}),
}


def _split_clauses(cypher: str) -> Tuple[Tuple[str, str], ...]:
    text = cypher.strip()
    if not text:
        return ()
    matches = list(_CLAUSE_RE.finditer(text))
    if not matches:
        return (("RAW", text),)
    clauses = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        clause = (match.group(1) or match.group(2)).upper()
        body = text[start:end].strip()
        clauses.append((clause, body))
    return tuple(clauses)


def _split_top_level(expr: str) -> Tuple[str, ...]:
    items = []
    buf = []
    depth = 0
    in_single = False
    in_double = False
    idx = 0
    while idx < len(expr):
        ch = expr[idx]
        if ch == "'" and not in_double:
            in_single = not in_single
            buf.append(ch)
        elif ch == '"' and not in_single:
            in_double = not in_double
            buf.append(ch)
        elif not in_single and not in_double:
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth = max(0, depth - 1)
            if ch == "," and depth == 0:
                item = "".join(buf).strip()
                if item:
                    items.append(item)
                buf = []
                idx += 1
                continue
            buf.append(ch)
        else:
            buf.append(ch)
        idx += 1
    tail = "".join(buf).strip()
    if tail:
        items.append(tail)
    return tuple(items)


def _split_top_level_keyword(expr: str, keyword: str) -> Optional[Tuple[str, str]]:
    txt = expr
    upper = txt.upper()
    needle = keyword.upper()
    depth_paren = 0
    depth_bracket = 0
    depth_brace = 0
    in_single = False
    in_double = False
    idx = 0
    while idx < len(txt):
        ch = txt[idx]
        if ch == "'" and not in_double:
            in_single = not in_single
            idx += 1
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            idx += 1
            continue
        if in_single or in_double:
            idx += 1
            continue
        if ch == "(":
            depth_paren += 1
            idx += 1
            continue
        if ch == ")":
            depth_paren = max(0, depth_paren - 1)
            idx += 1
            continue
        if ch == "[":
            depth_bracket += 1
            idx += 1
            continue
        if ch == "]":
            depth_bracket = max(0, depth_bracket - 1)
            idx += 1
            continue
        if ch == "{":
            depth_brace += 1
            idx += 1
            continue
        if ch == "}":
            depth_brace = max(0, depth_brace - 1)
            idx += 1
            continue
        if depth_paren == 0 and depth_bracket == 0 and depth_brace == 0 and upper.startswith(needle, idx):
            left_ok = idx == 0 or not (upper[idx - 1].isalnum() or upper[idx - 1] == "_")
            right_idx = idx + len(needle)
            right_ok = right_idx >= len(upper) or not (upper[right_idx].isalnum() or upper[right_idx] == "_")
            if left_ok and right_ok:
                left = txt[:idx].strip()
                right = txt[right_idx:].strip()
                if left and right:
                    return left, right
        idx += 1
    return None


def _strip_distinct(body: str) -> Tuple[bool, str]:
    if body.upper().startswith("DISTINCT "):
        return True, body[len("DISTINCT ") :].strip()
    return False, body


@dataclass(frozen=True)
class _Token:
    kind: str
    value: str


def _tokenize(expr: str) -> Tuple[_Token, ...]:
    tokens = []
    idx = 0
    while idx < len(expr):
        ch = expr[idx]
        if ch.isspace():
            idx += 1
            continue
        if ch in ("'", '"'):
            quote = ch
            idx += 1
            buf = []
            while idx < len(expr):
                ch = expr[idx]
                if ch == "\\":
                    if idx + 1 >= len(expr):
                        raise ValueError("unterminated escape sequence in string literal")
                    esc = expr[idx + 1]
                    if esc == "u":
                        if idx + 5 >= len(expr):
                            raise ValueError("invalid unicode escape in string literal")
                        hex_digits = expr[idx + 2 : idx + 6]
                        if re.fullmatch(r"[0-9A-Fa-f]{4}", hex_digits) is None:
                            raise ValueError("invalid unicode escape in string literal")
                        buf.append(chr(int(hex_digits, 16)))
                        idx += 6
                        continue
                    if esc == "n":
                        buf.append("\n")
                    elif esc == "t":
                        buf.append("\t")
                    elif esc == "r":
                        buf.append("\r")
                    elif esc == "b":
                        buf.append("\b")
                    elif esc == "f":
                        buf.append("\f")
                    elif esc in {"\\", "'", '"'}:
                        buf.append(esc)
                    else:
                        raise ValueError(f"unsupported escape sequence: \\{esc}")
                    idx += 2
                    continue
                if ch == quote:
                    idx += 1
                    break
                buf.append(ch)
                idx += 1
            tokens.append(_Token("STRING", "".join(buf)))
            continue
        if ch == "`":
            idx += 1
            buf = []
            while idx < len(expr) and expr[idx] != "`":
                buf.append(expr[idx])
                idx += 1
            if idx < len(expr) and expr[idx] == "`":
                idx += 1
            tokens.append(_Token("IDENT", "".join(buf)))
            continue
        if ch.isdigit():
            start = idx
            idx += 1
            while idx < len(expr) and expr[idx].isdigit():
                idx += 1
            if idx < len(expr) and expr[idx] == ".":
                idx += 1
                while idx < len(expr) and expr[idx].isdigit():
                    idx += 1
            tokens.append(_Token("NUMBER", expr[start:idx]))
            continue
        if ch == "$":
            idx += 1
            start = idx
            while idx < len(expr) and (expr[idx].isalnum() or expr[idx] == "_"):
                idx += 1
            tokens.append(_Token("PARAM", expr[start:idx]))
            continue
        if ch.isalpha() or ch == "_":
            start = idx
            idx += 1
            while idx < len(expr) and (expr[idx].isalnum() or expr[idx] == "_"):
                idx += 1
            while idx + 1 < len(expr) and expr[idx] == "." and (expr[idx + 1].isalpha() or expr[idx + 1] == "_"):
                idx += 1
                while idx < len(expr) and (expr[idx].isalnum() or expr[idx] == "_"):
                    idx += 1
            tokens.append(_Token("IDENT", expr[start:idx]))
            continue
        if expr.startswith(("<=", ">=", "<>", "!=", "=~"), idx):
            tokens.append(_Token("OP", expr[idx : idx + 2]))
            idx += 2
            continue
        if ch in "+-*/%^=<>":
            tokens.append(_Token("OP", ch))
            idx += 1
            continue
        if ch == "(":
            tokens.append(_Token("LPAREN", ch))
            idx += 1
            continue
        if ch == ")":
            tokens.append(_Token("RPAREN", ch))
            idx += 1
            continue
        if ch == "[":
            tokens.append(_Token("LBRACKET", ch))
            idx += 1
            continue
        if ch == "]":
            tokens.append(_Token("RBRACKET", ch))
            idx += 1
            continue
        if ch == "{":
            tokens.append(_Token("LBRACE", ch))
            idx += 1
            continue
        if ch == "}":
            tokens.append(_Token("RBRACE", ch))
            idx += 1
            continue
        if ch == ",":
            tokens.append(_Token("COMMA", ch))
            idx += 1
            continue
        if ch == ":":
            tokens.append(_Token("COLON", ch))
            idx += 1
            continue
        idx += 1
    tokens.append(_Token("EOF", ""))
    return tuple(tokens)


class _ExprParser:
    def __init__(self, tokens: Tuple[_Token, ...]) -> None:
        self.tokens = tokens
        self.index = 0

    def _peek(self, offset: int = 0) -> _Token:
        idx = min(self.index + offset, len(self.tokens) - 1)
        return self.tokens[idx]

    def _advance(self) -> _Token:
        tok = self._peek()
        self.index = min(self.index + 1, len(self.tokens))
        return tok

    def _match(self, kind: str, value: Optional[str] = None) -> bool:
        tok = self._peek()
        if tok.kind != kind:
            return False
        if value is not None and tok.value.upper() != value.upper():
            return False
        self._advance()
        return True

    def _peek_keyword(self, word: str, offset: int = 0) -> bool:
        tok = self._peek(offset)
        return tok.kind == "IDENT" and tok.value.upper() == word.upper()

    def _match_keyword(self, word: str) -> bool:
        if self._peek_keyword(word):
            self._advance()
            return True
        return False

    def _expect(self, kind: str, value: Optional[str] = None) -> None:
        if not self._match(kind, value):
            raise ValueError(f"Expected {kind} {value or ''}")

    def parse(self):
        return self._parse_or()

    def _parse_or(self):
        left = self._parse_xor()
        while self._match_keyword("OR"):
            right = self._parse_xor()
            left = binary("or", left, right)
        return left

    def _parse_xor(self):
        left = self._parse_and()
        while self._match_keyword("XOR"):
            right = self._parse_and()
            left = binary("xor", left, right)
        return left

    def _parse_and(self):
        left = self._parse_not()
        while self._match_keyword("AND"):
            right = self._parse_not()
            left = binary("and", left, right)
        return left

    def _parse_not(self):
        if self._match_keyword("NOT"):
            return unary("not", self._parse_not())
        return self._parse_comparison()

    def _parse_comparison(self):
        left = self._parse_add()
        while True:
            if self._match_keyword("IS"):
                if self._match_keyword("NOT"):
                    if not self._match_keyword("NULL"):
                        raise ValueError("Expected NULL after IS NOT")
                    left = unary("is_not_null", left)
                else:
                    if not self._match_keyword("NULL"):
                        raise ValueError("Expected NULL after IS")
                    left = unary("is_null", left)
                continue
            if self._peek_keyword("NOT") and self._peek_keyword("IN", offset=1):
                self._advance()
                self._advance()
                right = self._parse_add()
                left = binary("not_in", left, right)
                continue
            if self._peek_keyword("NOT") and self._peek_keyword("CONTAINS", offset=1):
                self._advance()
                self._advance()
                right = self._parse_add()
                left = binary("not_contains", left, right)
                continue
            if self._peek_keyword("NOT") and self._peek_keyword("STARTS", offset=1) and self._peek_keyword("WITH", offset=2):
                self._advance()
                self._advance()
                self._advance()
                right = self._parse_add()
                left = binary("not_starts_with", left, right)
                continue
            if self._peek_keyword("NOT") and self._peek_keyword("ENDS", offset=1) and self._peek_keyword("WITH", offset=2):
                self._advance()
                self._advance()
                self._advance()
                right = self._parse_add()
                left = binary("not_ends_with", left, right)
                continue
            if self._match_keyword("IN"):
                right = self._parse_add()
                left = binary("in", left, right)
                continue
            if self._match_keyword("CONTAINS"):
                right = self._parse_add()
                left = binary("contains", left, right)
                continue
            if self._peek_keyword("STARTS") and self._peek_keyword("WITH", offset=1):
                self._advance()
                self._advance()
                right = self._parse_add()
                left = binary("starts_with", left, right)
                continue
            if self._peek_keyword("ENDS") and self._peek_keyword("WITH", offset=1):
                self._advance()
                self._advance()
                right = self._parse_add()
                left = binary("ends_with", left, right)
                continue
            if self._match("OP", "="):
                right = self._parse_add()
                left = binary("eq", left, right)
                continue
            if self._match("OP", "<>") or self._match("OP", "!="):
                right = self._parse_add()
                left = binary("neq", left, right)
                continue
            if self._match("OP", "<="):
                right = self._parse_add()
                left = binary("lte", left, right)
                continue
            if self._match("OP", ">="):
                right = self._parse_add()
                left = binary("gte", left, right)
                continue
            if self._match("OP", "<"):
                right = self._parse_add()
                left = binary("lt", left, right)
                continue
            if self._match("OP", ">"):
                right = self._parse_add()
                left = binary("gt", left, right)
                continue
            if self._match("OP", "=~"):
                right = self._parse_add()
                left = binary("regex", left, right)
                continue
            break
        return left

    def _parse_add(self):
        left = self._parse_mul()
        while True:
            if self._match("OP", "+"):
                right = self._parse_mul()
                left = binary("add", left, right)
                continue
            if self._match("OP", "-"):
                right = self._parse_mul()
                left = binary("sub", left, right)
                continue
            break
        return left

    def _parse_mul(self):
        left = self._parse_pow()
        while True:
            if self._match("OP", "*"):
                right = self._parse_pow()
                left = binary("mul", left, right)
                continue
            if self._match("OP", "/"):
                right = self._parse_pow()
                left = binary("div", left, right)
                continue
            if self._match("OP", "%"):
                right = self._parse_pow()
                left = binary("mod", left, right)
                continue
            break
        return left

    def _parse_pow(self):
        left = self._parse_unary()
        if self._match("OP", "^"):
            right = self._parse_pow()
            return binary("pow", left, right)
        return left

    def _parse_unary(self):
        if self._match("OP", "+"):
            return unary("pos", self._parse_unary())
        if self._match("OP", "-"):
            return unary("neg", self._parse_unary())
        return self._parse_primary()

    def _parse_primary(self):
        tok = self._peek()
        if self._match("NUMBER"):
            if "." in tok.value:
                expr_val = lit(float(tok.value))
            else:
                expr_val = lit(int(tok.value))
        elif self._match("STRING"):
            expr_val = lit(tok.value)
        elif self._match("PARAM"):
            expr_val = param(tok.value)
        elif self._match("IDENT"):
            upper = tok.value.upper()
            if upper == "NULL":
                expr_val = lit(None)
            elif upper == "TRUE":
                expr_val = lit(True)
            elif upper == "FALSE":
                expr_val = lit(False)
            elif self._match("LPAREN"):
                args = []
                if not self._match("RPAREN"):
                    while True:
                        if self._match_keyword("DISTINCT"):
                            args.append(distinct_expr(self._parse_or()))
                        else:
                            args.append(self._parse_or())
                        if self._match("COMMA"):
                            continue
                        self._expect("RPAREN")
                        break
                expr_val = func(tok.value, args)
            else:
                expr_val = col(tok.value)
        elif self._match("OP", "*"):
            expr_val = star()
        elif self._match("LPAREN"):
            expr_val = self._parse_or()
            self._expect("RPAREN")
        elif self._match("LBRACKET"):
            items = []
            if not self._match("RBRACKET"):
                while True:
                    items.append(self._parse_or())
                    if self._match("COMMA"):
                        continue
                    self._expect("RBRACKET")
                    break
            expr_val = list_(items)
        elif self._match("LBRACE"):
            items = []
            if not self._match("RBRACE"):
                while True:
                    key_token = self._advance()
                    if key_token.kind not in ("IDENT", "STRING"):
                        raise ValueError("Expected map key")
                    key = key_token.value
                    self._expect("COLON")
                    value = self._parse_or()
                    items.append((key, value))
                    if self._match("COMMA"):
                        continue
                    self._expect("RBRACE")
                    break
            expr_val = map_(items)
        else:
            raise ValueError("Unexpected token in expression")

        while self._match("LBRACKET"):
            idx_expr = self._parse_or()
            self._expect("RBRACKET")
            expr_val = index(expr_val, idx_expr)
        return expr_val


def _parse_expr(expr_text: str):
    # Preserve Cypher slice syntax for downstream GFQL string delegation.
    # The lightweight parser tokenizes `1..3` as numeric/index fragments.
    if re.search(r"\[[^\]]*\.\.[^\]]*\]", expr_text):
        return raw(expr_text)
    try:
        tokens = _tokenize(expr_text)
        parser = _ExprParser(tokens)
        result = parser.parse()
        if parser._peek().kind != "EOF":
            raise ValueError("trailing tokens")
        return result
    except Exception:
        return raw(expr_text)


def _parse_return_items(body: str) -> Tuple[Tuple[str, object], ...]:
    items = []
    for item in _split_top_level(body):
        parts = re.split(r"(?i)\s+AS\s+", item, maxsplit=1)
        if len(parts) == 2:
            expr_text, alias = parts[0].strip(), parts[1].strip()
        else:
            expr_text = item.strip()
            alias = expr_text
        items.append((alias, _parse_expr(expr_text)))
    return tuple(items)


def _parse_order_by(body: str) -> Tuple[Tuple[object, str], ...]:
    items = []
    for item in _split_top_level(body):
        match = _ORDER_DIR_RE.match(item.strip())
        if match:
            expr_text = match.group("expr").strip()
            direction_raw = match.group("dir").strip().lower()
            direction = "asc" if direction_raw in {"asc", "ascending"} else "desc"
        else:
            expr_text = item.strip()
            direction = "asc"
        items.append((_parse_expr(expr_text), direction))
    return tuple(items)


def _parse_value(token: str):
    value = token.strip()
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)
    return value


def _plan_from_cypher(cypher: str) -> Tuple:
    steps = []
    for clause, body in _split_clauses(cypher):
        if clause in ("MATCH", "OPTIONAL MATCH"):
            steps.append(step("match", pattern=body, optional=(clause == "OPTIONAL MATCH")))
        elif clause == "WHERE":
            steps.append(step("where", expr=_parse_expr(body)))
        elif clause == "UNWIND":
            parts = re.split(r"(?i)\s+AS\s+", body, maxsplit=1)
            payload = {"expr": _parse_expr(parts[0].strip())}
            if len(parts) == 2:
                payload["as_"] = parts[1].strip()
            steps.append(step("unwind", **payload))
        elif clause == "WITH":
            distinct_flag, content = _strip_distinct(body)
            where_split = _split_top_level_keyword(content, "WHERE")
            with_items_text = where_split[0] if where_split is not None else content
            where_text = where_split[1] if where_split is not None else None
            steps.append(step("with", items=_parse_return_items(with_items_text)))
            if distinct_flag:
                steps.append(distinct())
            if where_text is not None:
                steps.append(step("where", expr=_parse_expr(where_text)))
        elif clause == "RETURN":
            distinct_flag, content = _strip_distinct(body)
            steps.append(select(_parse_return_items(content)))
            if distinct_flag:
                steps.append(distinct())
        elif clause == "ORDER BY":
            steps.append(order_by(_parse_order_by(body)))
        elif clause == "SKIP":
            steps.append(skip(_parse_value(body)))
        elif clause == "LIMIT":
            steps.append(limit(_parse_value(body)))
        else:
            steps.append(step(clause.lower().replace(" ", "_"), expr=body))
    if not steps:
        steps.append(step("raw", expr=cypher))
    return plan(*steps)


def _apply_translation(scenario: Scenario) -> Scenario:
    if scenario.status != "xfail":
        return scenario
    if scenario.gfql is not None:
        return scenario
    if "target-table-ops" in scenario.tags or "target-expr-dsl" in scenario.tags:
        return replace(scenario, gfql=_plan_from_cypher(scenario.cypher))
    return scenario


def _with_orderby_expected_order(scenario: Scenario) -> Optional[bool]:
    if not scenario.feature_path.startswith("tck/features/clauses/with-orderBy/"):
        return None
    feature_name = scenario.feature_path.rsplit("/", 1)[-1]
    ordered_scenarios = _WITH_ORDERBY_ORDERED_SCENARIO_NUMBERS.get(feature_name)
    if ordered_scenarios is None:
        return None
    match = _WITH_ORDERBY_KEY_RE.match(scenario.key)
    if match is None:
        return None
    scenario_number = int(match.group("scenario"))
    return scenario_number in ordered_scenarios


def _apply_expected_row_order(scenario: Scenario) -> Scenario:
    if scenario.expected.rows is None:
        return scenario
    ordered = _with_orderby_expected_order(scenario)
    if ordered is None:
        return scenario
    return replace(scenario, expected=replace(scenario.expected, ordered=ordered))


def _without_tag(tags: Tuple[str, ...], target: str) -> Tuple[str, ...]:
    return tuple(tag for tag in tags if tag != target)


def _is_executable_plan_tuple(gfql: object) -> bool:
    if not isinstance(gfql, tuple) or not gfql:
        return False
    if not all(isinstance(step_obj, PlanStep) for step_obj in gfql):
        return False
    if any(step_obj.op in {"raw", "invalid"} for step_obj in gfql):
        return False
    return True


def _is_error_plan_tuple(gfql: object) -> bool:
    if not isinstance(gfql, tuple) or not gfql:
        return False
    if not all(isinstance(step_obj, PlanStep) for step_obj in gfql):
        return False
    return not any(step_obj.op == "raw" for step_obj in gfql)


def _promote_executor_support(scenario: Scenario) -> Scenario:
    if scenario.status != "xfail":
        return scenario
    supports_rows = scenario.key in PHASE1_EXECUTOR_SUPPORTED_KEYS and scenario.expected.rows is not None
    supports_error = scenario.key in PHASE1_EXECUTOR_SUPPORTED_ERROR_KEYS and scenario.expected.rows is None
    if not supports_rows and not supports_error:
        return scenario

    if supports_rows and not _is_executable_plan_tuple(scenario.gfql):
        return scenario
    if supports_error and not _is_error_plan_tuple(scenario.gfql):
        return scenario

    tags = list(_without_tag(scenario.tags, "xfail"))
    if "phase1-executor" not in tags:
        tags.append("phase1-executor")
    if supports_error and "phase1-executor-error" not in tags:
        tags.append("phase1-executor-error")

    pure_row = scenario.key in PHASE1_EXECUTOR_PURE_KEYS
    pure_error = scenario.key in PHASE1_EXECUTOR_PURE_ERROR_KEYS
    if (pure_row or pure_error) and "phase1-executor-pure" not in tags:
        tags.append("phase1-executor-pure")

    return replace(
        scenario,
        status="supported",
        reason=None,
        tags=tuple(tags),
    )




def _promote_cypher_string_support(scenario: Scenario) -> Scenario:
    if scenario.status != "xfail":
        return scenario

    supports_success = (
        scenario.key in DIRECT_CYPHER_PROMOTION_ROW_KEYS
        and (
            scenario.expected.rows is not None
            or scenario.expected.node_ids is not None
            or scenario.expected.edge_ids is not None
        )
    )
    supports_error = (
        scenario.key in DIRECT_CYPHER_PROMOTION_ERROR_KEYS
        and scenario.expected.rows is None
    )
    if not supports_success and not supports_error:
        return scenario

    tags = list(_without_tag(scenario.tags, "xfail"))
    if "cypher-string" not in tags:
        tags.append("cypher-string")
    if "cypher-string-pure" not in tags:
        tags.append("cypher-string-pure")
    if supports_error and "cypher-string-error" not in tags:
        tags.append("cypher-string-error")

    return replace(
        scenario,
        status="supported",
        reason=None,
        tags=tuple(tags),
    )

for path in sorted(_SCENARIO_ROOT.rglob("*.py"), key=lambda p: p.as_posix()):
    module_name = "tests.cypher_tck.scenarios." + path.relative_to(Path(__file__).resolve().parent).with_suffix("").as_posix().replace("/", ".")
    spec = spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        continue
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    SCENARIOS.extend(getattr(module, "SCENARIOS", []))

SCENARIOS = [
    _promote_cypher_string_support(
        _promote_executor_support(
            _apply_translation(_apply_expected_row_order(_tag_scenario(scenario)))
        )
    )
    for scenario in SCENARIOS
]
