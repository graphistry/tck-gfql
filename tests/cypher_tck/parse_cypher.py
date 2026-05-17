import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Tuple

from tests.cypher_tck.models import GraphFixture


@dataclass
class ParseContext:
    nodes_by_id: Dict[str, Dict[str, Any]]
    var_to_id: Dict[str, str]
    node_counter: int
    rel_counter: int


_CREATE_SPLIT_RE = re.compile(r"\bCREATE\b", flags=re.IGNORECASE)
_UNWIND_PREFIX_RE = re.compile(
    r"^\s*UNWIND\s+(?P<expr>\[[\s\S]*?\])\s+AS\s+(?P<var>[A-Za-z_][A-Za-z0-9_]*)\s+(?P<body>[\s\S]+)$",
    flags=re.IGNORECASE,
)

_PROPERTY_REF_RE = re.compile(
    r"^([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)$"
)
_UNRESOLVED_REF = object()


def _split_top_level(text: str) -> List[str]:
    parts: List[str] = []
    buf: List[str] = []
    depth_paren = 0
    depth_brace = 0
    depth_bracket = 0
    in_quote = False
    for ch in text:
        if ch == "'":
            in_quote = not in_quote
        if not in_quote:
            if ch == '(':
                depth_paren += 1
            elif ch == ')':
                depth_paren = max(depth_paren - 1, 0)
            elif ch == '{':
                depth_brace += 1
            elif ch == '}':
                depth_brace = max(depth_brace - 1, 0)
            elif ch == '[':
                depth_bracket += 1
            elif ch == ']':
                depth_bracket = max(depth_bracket - 1, 0)
        if ch == ',' and not in_quote and depth_paren == 0 and depth_brace == 0 and depth_bracket == 0:
            part = ''.join(buf).strip()
            if part:
                parts.append(part)
            buf = []
            continue
        buf.append(ch)
    tail = ''.join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


def _extract_balanced(text: str, open_ch: str, close_ch: str) -> Tuple[str, str]:
    depth = 0
    start = None
    in_quote = False
    for idx, ch in enumerate(text):
        if ch == "'":
            in_quote = not in_quote
        if in_quote:
            continue
        if ch == open_ch:
            if depth == 0:
                start = idx
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0 and start is not None:
                return text[start : idx + 1], text[idx + 1 :]
    raise ValueError(f"Unbalanced {open_ch}{close_ch} in: {text}")


def _split_key_value(item: str) -> Tuple[str, str] | None:
    depth_paren = 0
    depth_brace = 0
    depth_bracket = 0
    in_quote = False
    for idx, ch in enumerate(item):
        if ch == "'":
            in_quote = not in_quote
            continue
        if in_quote:
            continue
        if ch == "(":
            depth_paren += 1
            continue
        if ch == ")":
            depth_paren = max(depth_paren - 1, 0)
            continue
        if ch == "{":
            depth_brace += 1
            continue
        if ch == "}":
            depth_brace = max(depth_brace - 1, 0)
            continue
        if ch == "[":
            depth_bracket += 1
            continue
        if ch == "]":
            depth_bracket = max(depth_bracket - 1, 0)
            continue
        if (
            ch == ":"
            and depth_paren == 0
            and depth_brace == 0
            and depth_bracket == 0
        ):
            key = item[:idx].strip()
            value = item[idx + 1 :].strip()
            return key, value
    return None


def _resolve_property_reference(token: str, ctx: "ParseContext | None") -> Any:
    """Resolve a `<var>.<prop>` reference to a previously-created node's property.

    Within a single CREATE, variables created earlier are in scope, so e.g.
    ``CREATE (a:End {id: 0}), (:Begin {num: a.id})`` should give the Begin node
    ``num = 0``.  Returns ``_UNRESOLVED_REF`` when the token is not a property
    reference or the referenced node/property is not (yet) known.
    """
    if ctx is None:
        return _UNRESOLVED_REF
    match = _PROPERTY_REF_RE.match(token)
    if match is None:
        return _UNRESOLVED_REF
    var, prop = match.group(1), match.group(2)
    node_id = ctx.var_to_id.get(var)
    if node_id is None:
        return _UNRESOLVED_REF
    node = ctx.nodes_by_id.get(node_id)
    if node is None or prop not in node:
        return _UNRESOLVED_REF
    return node[prop]


def _parse_literal(
    raw: str,
    bindings: Mapping[str, Any],
    ctx: "ParseContext | None" = None,
) -> Any:
    token = raw.strip()
    if token in bindings:
        return bindings[token]
    if token.startswith("'") and token.endswith("'"):
        return token[1:-1]
    if re.fullmatch(r"-?\d+", token):
        return int(token)
    if re.fullmatch(r"-?\d+\.\d+", token):
        return float(token)
    if token.lower() == "null":
        return None
    if token.lower() in {"true", "false"}:
        return token.lower() == "true"
    if token.startswith("[") and token.endswith("]"):
        inner = token[1:-1].strip()
        if not inner:
            return []
        return [_parse_literal(part, bindings, ctx) for part in _split_top_level(inner)]
    if token.startswith("{") and token.endswith("}"):
        return _parse_properties(token, bindings, ctx)
    resolved = _resolve_property_reference(token, ctx)
    if resolved is not _UNRESOLVED_REF:
        return resolved
    return token


def _parse_properties(
    prop_text: str,
    bindings: Mapping[str, Any],
    ctx: "ParseContext | None" = None,
) -> Dict[str, Any]:
    props: Dict[str, Any] = {}
    inner = prop_text.strip()[1:-1].strip()
    if not inner:
        return props
    items = _split_top_level(inner)
    for item in items:
        pair = _split_key_value(item)
        if pair is None:
            continue
        key, raw = pair
        props[key] = _parse_literal(raw, bindings, ctx)
    return props


def _parse_node(node_text: str, ctx: ParseContext, bindings: Mapping[str, Any]) -> str:
    inner = node_text.strip()[1:-1].strip()
    props: Dict[str, Any] = {}
    if '{' in inner:
        before, prop_part = inner.split('{', 1)
        inner = before.strip()
        props = _parse_properties('{' + prop_part, bindings, ctx)
    var: str | None = None
    labels: List[str] = []
    if inner:
        if inner.startswith(':'):
            var_part = ''
            label_part = inner
        else:
            var_part, *rest = inner.split(':')
            label_part = ':' + ':'.join(rest) if rest else ''
        var_part = var_part.strip()
        if var_part:
            var = var_part
        if label_part:
            labels = [lab for lab in label_part.split(':') if lab]
    if var and var in ctx.var_to_id:
        node_id = ctx.var_to_id[var]
    else:
        node_id = var or f"anon_{ctx.node_counter}"
        ctx.node_counter += 1
        if var:
            ctx.var_to_id[var] = node_id
    if node_id in ctx.nodes_by_id:
        node = ctx.nodes_by_id[node_id]
        existing_labels = list(node.get("labels", []))
        for lab in labels:
            if lab not in existing_labels:
                existing_labels.append(lab)
        node["labels"] = existing_labels
        for key, value in props.items():
            node.setdefault(key, value)
    else:
        node = {"id": node_id, "labels": labels, **props}
        ctx.nodes_by_id[node_id] = node
    return node_id


def _parse_rel_segment(
    rel_segment: str,
    ctx: ParseContext,
    bindings: Mapping[str, Any],
) -> Tuple[str, str | None, Dict[str, Any]]:
    rel_inner = rel_segment.strip()[1:-1].strip()
    rel_props: Dict[str, Any] = {}
    if '{' in rel_inner:
        before, prop_part = rel_inner.split('{', 1)
        rel_inner = before.strip()
        rel_props = _parse_properties('{' + prop_part, bindings, ctx)
    rel_var = None
    rel_type = None
    if rel_inner:
        rel_parts = rel_inner.split(':')
        rel_var = rel_parts[0].strip() or None
        if len(rel_parts) > 1:
            rel_type = rel_parts[1].strip() or None
    edge_id = rel_var or f"rel_{ctx.rel_counter}"
    ctx.rel_counter += 1
    return edge_id, rel_type, rel_props


def _edge_from_segment(
    left_id: str,
    right_id: str,
    rel_segment: str,
    left_dir: str | None,
    right_dir: str | None,
    ctx: ParseContext,
    bindings: Mapping[str, Any],
) -> Dict[str, Any]:
    edge_id, rel_type, rel_props = _parse_rel_segment(rel_segment, ctx, bindings)
    if left_dir == '<-' and right_dir == '-':
        src, dst = right_id, left_id
    elif left_dir == '-' and right_dir == '->':
        src, dst = left_id, right_id
    elif left_dir == '<-' and right_dir == '->':
        src, dst = right_id, left_id
    else:
        src, dst = left_id, right_id
    edge = {
        "edge_id": edge_id,
        "src": src,
        "dst": dst,
        "type": rel_type,
        "undirected": left_dir == '-' and right_dir == '-',
    }
    for key, value in rel_props.items():
        if key in edge:
            edge[f"prop__{key}"] = value
        else:
            edge[key] = value
    return edge


def _parse_chain(pattern: str, ctx: ParseContext, bindings: Mapping[str, Any]) -> List[Dict[str, Any]]:
    edges: List[Dict[str, Any]] = []
    node_text, rest = _extract_balanced(pattern.strip(), '(', ')')
    left_id = _parse_node(node_text, ctx, bindings)
    text = rest.strip()
    while text:
        left_dir = None
        if text.startswith('<-'):
            left_dir = '<-'
            text = text[2:]
        elif text.startswith('-'):
            left_dir = '-'
            text = text[1:]
        else:
            break

        rel_segment, rest = _extract_balanced(text.strip(), '[', ']')
        text = rest.strip()

        right_dir = None
        if text.startswith('->'):
            right_dir = '->'
            text = text[2:]
        elif text.startswith('-'):
            right_dir = '-'
            text = text[1:]

        node_text, rest = _extract_balanced(text.strip(), '(', ')')
        right_id = _parse_node(node_text, ctx, bindings)
        text = rest.strip()

        edges.append(_edge_from_segment(left_id, right_id, rel_segment, left_dir, right_dir, ctx, bindings))
        left_id = right_id
    return edges


def _extract_create_clauses(script: str) -> List[str]:
    parts = _CREATE_SPLIT_RE.split(script)
    clauses: List[str] = []
    for part in parts[1:]:
        clause = part.strip()
        if clause:
            clauses.append(clause)
    return clauses


def _normalize_script(script: str) -> str:
    parts: List[str] = []
    in_quote = False
    whitespace_pending = False

    for ch in script.strip():
        if ch == "'":
            if whitespace_pending and not in_quote and parts:
                parts.append(" ")
            whitespace_pending = False
            in_quote = not in_quote
            parts.append(ch)
            continue

        if in_quote:
            parts.append(ch)
            continue

        if ch.isspace():
            whitespace_pending = True
            continue

        if whitespace_pending and parts:
            parts.append(" ")
        whitespace_pending = False
        parts.append(ch)

    return "".join(parts).strip()


def _extract_unwind_bindings(script: str) -> Tuple[List[Dict[str, Any]], str]:
    normalized = _normalize_script(script)
    match = _UNWIND_PREFIX_RE.match(normalized)
    if match is None:
        return [{}], normalized

    unwind_values = _parse_literal(match.group("expr"), {})
    if not isinstance(unwind_values, list):
        return [{}], normalized

    var_name = match.group("var")
    body = match.group("body").strip()
    bindings = [{var_name: value} for value in unwind_values]
    if not bindings:
        return [], body
    return bindings, body


def graph_fixture_from_create(script: str) -> GraphFixture:
    bindings_list, create_script = _extract_unwind_bindings(script)
    if not bindings_list:
        return GraphFixture(nodes=[], edges=[], edge_columns=("src", "dst", "edge_id", "type", "undirected"))

    ctx = ParseContext(nodes_by_id={}, var_to_id={}, node_counter=1, rel_counter=1)
    edges: List[Dict[str, Any]] = []
    for bindings in bindings_list:
        for clause in _extract_create_clauses(create_script):
            for pattern in _split_top_level(clause):
                if '[' in pattern and ']' in pattern:
                    edges.extend(_parse_chain(pattern, ctx, bindings))
                else:
                    _parse_node(pattern, ctx, bindings)
    return GraphFixture(
        nodes=list(ctx.nodes_by_id.values()),
        edges=edges,
        edge_columns=("src", "dst", "edge_id", "type", "undirected"),
    )


def merge_fixtures(fixtures: Iterable[GraphFixture]) -> GraphFixture:
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    for fixture in fixtures:
        nodes.extend(fixture.nodes)
        edges.extend(fixture.edges)
    return GraphFixture(nodes=nodes, edges=edges)
