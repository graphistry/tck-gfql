from tests.cypher_tck.parse_cypher import graph_fixture_from_create


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
    nodes = {node["id"]: node for node in fixture.nodes}
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
    source = next(node for node in fixture.nodes if node["id"] == "a")
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
