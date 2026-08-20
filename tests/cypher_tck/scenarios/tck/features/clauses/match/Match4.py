from graphistry.compute import e_forward, e_undirected, n

from tests.cypher_tck.models import Expected, GraphFixture, Scenario
from tests.cypher_tck.parse_cypher import graph_fixture_from_create

from tests.cypher_tck.scenarios.fixtures import (
    MATCH5_GRAPH,
    MATCH7_GRAPH_SINGLE,
    MATCH7_GRAPH_AB,
    MATCH7_GRAPH_ABC,
    MATCH7_GRAPH_REL,
    MATCH7_GRAPH_X,
    MATCH7_GRAPH_AB_X,
    MATCH7_GRAPH_LABELS,
    MATCH7_GRAPH_PLAYER_TEAM_BOTH,
    MATCH7_GRAPH_PLAYER_TEAM_SINGLE,
    MATCH7_GRAPH_PLAYER_TEAM_DIFF,
    WITH_ORDERBY4_GRAPH,
    BINARY_TREE_1_GRAPH,
    BINARY_TREE_2_GRAPH,
)


SCENARIOS = [
    Scenario(
        key="match4-1",
        feature_path="tck/features/clauses/match/Match4.feature",
        scenario="[1] Handling fixed-length variable length pattern",
        cypher="MATCH (a)-[r*1..1]->(b)\nRETURN r",
        graph=graph_fixture_from_create(
            """
            CREATE ()-[:T]->()
            """
        ),
        expected=Expected(
            rows=[
                {"r": "[[:T]]"},
            ],
        ),
        gfql=None,
        status="xfail",
        reason="Variable-length relationship matching and row projections are not supported",
        tags=("match", "variable-length", "xfail"),
    ),

    Scenario(
        key="match4-2",
        feature_path="tck/features/clauses/match/Match4.feature",
        scenario="[2] Simple variable length pattern",
        cypher="MATCH (a {name: 'A'})-[*]->(x)\nRETURN x",
        graph=graph_fixture_from_create(
            """
            CREATE (a {name: 'A'}), (b {name: 'B'}),
                   (c {name: 'C'}), (d {name: 'D'})
            CREATE (a)-[:CONTAINS]->(b),
                   (b)-[:CONTAINS]->(c),
                   (c)-[:CONTAINS]->(d)
            """
        ),
        expected=Expected(
            rows=[
                {"x": "({name: 'B'})"},
                {"x": "({name: 'C'})"},
                {"x": "({name: 'D'})"},
            ],
        ),
        gfql=None,
        status="xfail",
        reason="Variable-length relationship matching is not supported",
        tags=("match", "variable-length", "xfail"),
    ),

    Scenario(
        key="match4-3",
        feature_path="tck/features/clauses/match/Match4.feature",
        scenario="[3] Zero-length variable length pattern in the middle of the pattern",
        cypher="MATCH (a {name: 'A'})-[:CONTAINS*0..1]->(b)-[:FRIEND*0..1]->(c)\nRETURN a, b, c",
        graph=graph_fixture_from_create(
            """
            CREATE (a {name: 'A'}), (b {name: 'B'}),
                   (c {name: 'C'}), ({name: 'D'}),
                   ({name: 'E'})
            CREATE (a)-[:CONTAINS]->(b),
                   (b)-[:FRIEND]->(c)
            """
        ),
        expected=Expected(
            rows=[
                {"a": "({name: 'A'})", "b": "({name: 'A'})", "c": "({name: 'A'})"},
                {"a": "({name: 'A'})", "b": "({name: 'B'})", "c": "({name: 'B'})"},
                {"a": "({name: 'A'})", "b": "({name: 'B'})", "c": "({name: 'C'})"},
            ],
        ),
        gfql=None,
        status="xfail",
        reason="Variable-length relationship matching and row projections are not supported",
        tags=("match", "variable-length", "xfail"),
    ),

    Scenario(
        key="match4-4",
        feature_path="tck/features/clauses/match/Match4.feature",
        scenario="[4] Matching longer variable length paths",
        cypher="MATCH (n {var: 'start'})-[:T*]->(m {var: 'end'})\nRETURN m",
        # Upstream builds this chain with `UNWIND range(1, 20)` + `collect`; the
        # setup is deterministic, so it is expanded here as the explicit
        # 22-node / 21-edge `start -> 1..20 -> end` path it denotes.
        graph=graph_fixture_from_create(
            """
            CREATE (a {var: 'start'}), (b {var: 'end'}),
                   (n1 {var: 1}), (n2 {var: 2}), (n3 {var: 3}),
                   (n4 {var: 4}), (n5 {var: 5}), (n6 {var: 6}),
                   (n7 {var: 7}), (n8 {var: 8}), (n9 {var: 9}),
                   (n10 {var: 10}), (n11 {var: 11}), (n12 {var: 12}),
                   (n13 {var: 13}), (n14 {var: 14}), (n15 {var: 15}),
                   (n16 {var: 16}), (n17 {var: 17}), (n18 {var: 18}),
                   (n19 {var: 19}), (n20 {var: 20})
            CREATE (a)-[:T]->(n1),
                   (n1)-[:T]->(n2),
                   (n2)-[:T]->(n3),
                   (n3)-[:T]->(n4),
                   (n4)-[:T]->(n5),
                   (n5)-[:T]->(n6),
                   (n6)-[:T]->(n7),
                   (n7)-[:T]->(n8),
                   (n8)-[:T]->(n9),
                   (n9)-[:T]->(n10),
                   (n10)-[:T]->(n11),
                   (n11)-[:T]->(n12),
                   (n12)-[:T]->(n13),
                   (n13)-[:T]->(n14),
                   (n14)-[:T]->(n15),
                   (n15)-[:T]->(n16),
                   (n16)-[:T]->(n17),
                   (n17)-[:T]->(n18),
                   (n18)-[:T]->(n19),
                   (n19)-[:T]->(n20),
                   (n20)-[:T]->(b)
            """
        ),
        expected=Expected(
            rows=[
                {"m": "({var: 'end'})"},
            ],
        ),
        gfql=None,
        status="supported",
        tags=("match", "variable-length", "cypher-string", "cypher-string-pure"),
    ),

    Scenario(
        key="match4-5",
        feature_path="tck/features/clauses/match/Match4.feature",
        scenario="[5] Matching variable length pattern with property predicate",
        cypher="MATCH (a:Artist)-[:WORKED_WITH* {year: 1988}]->(b:Artist)\nRETURN *",
        graph=graph_fixture_from_create(
            """
            CREATE (a:Artist:A), (b:Artist:B), (c:Artist:C)
            CREATE (a)-[:WORKED_WITH {year: 1987}]->(b),
                   (b)-[:WORKED_WITH {year: 1988}]->(c)
            """
        ),
        expected=Expected(
            rows=[
                {"a": "(:Artist:B)", "b": "(:Artist:C)"},
            ],
        ),
        gfql=None,
        status="xfail",
        reason="Variable-length relationship matching and row projections are not supported",
        tags=("match", "variable-length", "xfail"),
    ),

    Scenario(
        key="match4-6",
        feature_path="tck/features/clauses/match/Match4.feature",
        scenario="[6] Matching variable length patterns from a bound node",
        cypher="MATCH (a:A)\nMATCH (a)-[r*2]->()\nRETURN r",
        graph=graph_fixture_from_create(
            """
            CREATE (a:A), (b), (c)
            CREATE (a)-[:X]->(b),
                   (b)-[:Y]->(c)
            """
        ),
        expected=Expected(
            rows=[
                {"r": "[[:X], [:Y]]"},
            ],
        ),
        gfql=None,
        status="xfail",
        reason="Variable-length relationship matching and list projections are not supported",
        tags=("match", "variable-length", "xfail"),
    ),

    Scenario(
        key="match4-7",
        feature_path="tck/features/clauses/match/Match4.feature",
        scenario="[7] Matching variable length patterns including a bound relationship",
        cypher="MATCH ()-[r:EDGE]-()\nMATCH p = (n)-[*0..1]-()-[r]-()-[*0..1]-(m)\nRETURN count(p) AS c",
        graph=graph_fixture_from_create(
            """
            CREATE (n0:Node),
                   (n1:Node),
                   (n2:Node),
                   (n3:Node),
                   (n0)-[:EDGE]->(n1),
                   (n1)-[:EDGE]->(n2),
                   (n2)-[:EDGE]->(n3)
            """
        ),
        expected=Expected(
            rows=[
                {"c": 32},
            ],
        ),
        gfql=None,
        status="xfail",
        reason="Variable-length relationship matching and aggregations are not supported",
        tags=("match", "variable-length", "aggregation", "xfail"),
    ),

    Scenario(
        key="match4-8",
        feature_path="tck/features/clauses/match/Match4.feature",
        scenario="[8] Matching relationships into a list and matching variable length using the list",
        cypher="MATCH ()-[r1]->()-[r2]->()\nWITH [r1, r2] AS rs\n  LIMIT 1\nMATCH (first)-[rs*]->(second)\nRETURN first, second",
        graph=graph_fixture_from_create(
            """
            CREATE (a:A), (b:B), (c:C)
            CREATE (a)-[:Y]->(b),
                   (b)-[:Y]->(c)
            """
        ),
        expected=Expected(
            rows=[
                {"first": "(:A)", "second": "(:C)"},
            ],
        ),
        gfql=None,
        status="xfail",
        reason="WITH pipelines, list relationship variables, and variable-length matching are not supported",
        tags=("match", "variable-length", "with", "xfail"),
    ),

    Scenario(
        key="match4-9",
        feature_path="tck/features/clauses/match/Match4.feature",
        scenario="[9] Fail when asterisk operator is missing",
        cypher="MATCH (a:A)\nMATCH (a)-[:LIKES..]->(c)\nRETURN c.name",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(),
        gfql=None,
        status="xfail",
        reason="Compile-time validation for invalid relationship patterns is not enforced",
        tags=("match", "syntax-error", "xfail"),
    ),

    Scenario(
        key="match4-10",
        feature_path="tck/features/clauses/match/Match4.feature",
        scenario="[10] Fail on negative bound",
        cypher="MATCH (a:A)\nMATCH (a)-[:LIKES*-2]->(c)\nRETURN c.name",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(),
        gfql=None,
        status="xfail",
        reason="Compile-time validation for invalid relationship patterns is not enforced",
        tags=("match", "syntax-error", "xfail"),
    ),
]
