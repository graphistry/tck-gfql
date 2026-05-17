from tests.cypher_tck.parse_cypher import graph_fixture_from_create
from tests.cypher_tck.scenarios import _plan_from_cypher


def test_parse_create_nodes_only():
    script = """
    CREATE (:A), (:B {name: 'b'}), ({name: 'c'})
    """
    fixture = graph_fixture_from_create(script)
    nodes = fixture.nodes
    assert len(nodes) == 3
    labels = {tuple(node.get("labels", [])) for node in nodes}
    assert ("A",) in labels
    assert ("B",) in labels
    assert () in labels
    by_name = {node.get("name"): node for node in nodes}
    assert "b" in by_name
    assert "c" in by_name


def test_parse_create_relationship():
    script = """
    CREATE (a:A {name: 'a'}), (b:B)
    CREATE (a)-[:KNOWS]->(b)
    """
    fixture = graph_fixture_from_create(script)
    nodes = {node[fixture.node_id]: node for node in fixture.nodes}
    assert set(nodes) == {"a", "b"}
    assert nodes["a"].get("labels") == ["A"]
    assert nodes["b"].get("labels") == ["B"]

    assert len(fixture.edges) == 1
    edge = fixture.edges[0]
    assert edge["src"] == "a"
    assert edge["dst"] == "b"
    assert edge["type"] == "KNOWS"


def test_parse_create_relationship_chain():
    script = """
    CREATE ({name: 'Someone'})<-[:X]-()-[:X]->({name: 'Andres'})
    """
    fixture = graph_fixture_from_create(script)
    assert len(fixture.nodes) == 3
    assert len(fixture.edges) == 2
    types = {edge["type"] for edge in fixture.edges}
    assert types == {"X"}


def test_parse_create_relationship_properties():
    script = """
    CREATE (a)-[:T {name: 'bar', weight: 2}]->(b)
    """
    fixture = graph_fixture_from_create(script)
    assert len(fixture.edges) == 1
    edge = fixture.edges[0]
    assert edge["type"] == "T"
    assert edge["name"] == "bar"
    assert edge["weight"] == 2


def test_parse_create_nested_list_and_map_literals() -> None:
    script = """
    CREATE (a:A {payload: [1, -2, true, null, 'z', {k: [3, 4]}], meta: {rank: 7, tags: ['x', 'y']}})
    CREATE (a)-[:R {attrs: {score: 1.5, flags: [false, true]}}]->(:B)
    """
    fixture = graph_fixture_from_create(script)
    assert len(fixture.nodes) == 2
    source = next(node for node in fixture.nodes if node[fixture.node_id] == "a")
    assert source["payload"] == [1, -2, True, None, "z", {"k": [3, 4]}]
    assert source["meta"] == {"rank": 7, "tags": ["x", "y"]}
    assert len(fixture.edges) == 1
    edge = fixture.edges[0]
    assert edge["attrs"] == {"score": 1.5, "flags": [False, True]}


def test_parse_create_preserves_newlines_inside_string_literals() -> None:
    script = """
    CREATE (:TheLabel {name: 'Foo Foo'}),
           (:TheLabel {name: 'Foo
Foo'}),
           (:TheLabel {name: 'Foo\tFoo'})
    """
    fixture = graph_fixture_from_create(script)
    names = [node.get("name") for node in fixture.nodes]
    assert names == ["Foo Foo", "Foo\nFoo", "Foo\tFoo"]


def test_parse_unwind_create_scalar_expansion() -> None:
    script = """
    UNWIND [1, 2, 3] AS i
    CREATE ({num: i})
    """
    fixture = graph_fixture_from_create(script)
    nums = sorted(node.get("num") for node in fixture.nodes)
    assert nums == [1, 2, 3]


def test_parse_unwind_create_string_expansion() -> None:
    script = """
    UNWIND ['a', 'b', 'c'] AS c
    CREATE ({name: c})
    """
    fixture = graph_fixture_from_create(script)
    names = sorted(node.get("name") for node in fixture.nodes)
    assert names == ["a", "b", "c"]


def test_parse_create_resolves_node_property_reference() -> None:
    script = """
    CREATE (a:End {num: 42, id: 0}),
           (:End {num: 3}),
           (:Begin {num: a.id})
    """
    fixture = graph_fixture_from_create(script)
    begin = next(node for node in fixture.nodes if node.get("labels") == ["Begin"])
    assert begin["num"] == 0


def test_parse_create_preserves_id_property_separate_from_node_identity() -> None:
    script = """
    CREATE (a:End {num: 42, id: 0}),
           (:End {num: 3}),
           (:Begin {num: a.id})
    """
    fixture = graph_fixture_from_create(script)
    assert fixture.node_id == "__node__"
    assert fixture.node_columns == ("__node__", "labels")

    nodes = {node[fixture.node_id]: node for node in fixture.nodes}
    assert set(nodes) == {"a", "anon_2", "anon_3"}
    assert nodes["a"]["id"] == 0
    assert nodes["a"]["num"] == 42
    assert nodes["anon_3"]["num"] == 0


def test_parse_unwind_create_resolves_map_property_reference() -> None:
    script = """
    UNWIND [{id: 1, year: 2024}, {id: 2, year: 2025}] AS event
    CREATE (:Event {id: event.id, year: event.year})
    """
    fixture = graph_fixture_from_create(script)
    rows = sorted((node["id"], node["year"]) for node in fixture.nodes)
    assert rows == [(1, 2024), (2, 2025)]


def test_parse_unwind_empty_uses_reserved_identity_columns() -> None:
    script = """
    UNWIND [] AS event
    CREATE (:Event {id: event.id})
    """
    fixture = graph_fixture_from_create(script)
    assert fixture.nodes == []
    assert fixture.node_id == "__node__"
    assert fixture.node_columns == ("__node__", "labels")


def test_plan_from_cypher_splits_order_by_skip_on_same_line() -> None:
    cypher = """
    MATCH ()-[r1]->(x)
    WITH x, sum(r1.num) AS c
      ORDER BY c SKIP 1
    RETURN x, c
    """
    ops = tuple(step.op for step in _plan_from_cypher(cypher))
    assert ops == ("match", "with", "order_by", "skip", "select")


def test_plan_from_cypher_splits_order_by_limit_on_same_line() -> None:
    cypher = """
    MATCH ()-[r1]->(x)
    WITH x, sum(r1.num) AS c
      ORDER BY c LIMIT 1
    RETURN x, c
    """
    ops = tuple(step.op for step in _plan_from_cypher(cypher))
    assert ops == ("match", "with", "order_by", "limit", "select")
