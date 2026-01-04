from graphistry.compute import e_forward, e_undirected, n

from tests.cypher_tck.gfql_plan import (
    match,
    order_by,
    plan,
    rows,
    select,
    skip,
    step,
)

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
        key="return-skip-limit1-1",
        feature_path="tck/features/clauses/return-skip-limit/ReturnSkipLimit1.feature",
        scenario="[1] Start the result from the second row",
        cypher="MATCH (n)\nRETURN n\nORDER BY n.name ASC\nSKIP 2",
        graph=graph_fixture_from_create(
            """
            CREATE ({name: 'A'}),
              ({name: 'B'}),
              ({name: 'C'}),
              ({name: 'D'}),
              ({name: 'E'})
            """
        ),
        expected=Expected(
            rows=[
                {"n": "({name: 'C'})"},
                {"n": "({name: 'D'})"},
                {"n": "({name: 'E'})"},
            ],
        ),
        gfql=plan(
            match(n(name="n")),
            rows(table="nodes", source="n"),
            select([("n", "n")]),
            order_by([("n.name", "asc")]),
            skip(2),
        ),
        status="xfail",
        reason="SKIP and ORDER BY are not supported",
        tags=("return", "skip", "orderby", "xfail"),
    ),

    Scenario(
        key="return-skip-limit1-2",
        feature_path="tck/features/clauses/return-skip-limit/ReturnSkipLimit1.feature",
        scenario="[2] Start the result from the second row by param",
        cypher="MATCH (n)\nRETURN n\nORDER BY n.name ASC\nSKIP $skipAmount",
        graph=graph_fixture_from_create(
            """
            CREATE ({name: 'A'}),
              ({name: 'B'}),
              ({name: 'C'}),
              ({name: 'D'}),
              ({name: 'E'})
            """
        ),
        expected=Expected(
            rows=[
                {"n": "({name: 'C'})"},
                {"n": "({name: 'D'})"},
                {"n": "({name: 'E'})"},
            ],
        ),
        gfql=plan(
            match(n(name="n")),
            rows(table="nodes", source="n"),
            select([("n", "n")]),
            order_by([("n.name", "asc")]),
            skip("$skipAmount"),
        ),
        status="xfail",
        reason="SKIP, ORDER BY, and parameter binding are not supported",
        tags=("return", "skip", "orderby", "params", "xfail"),
    ),

    Scenario(
        key="return-skip-limit1-3",
        feature_path="tck/features/clauses/return-skip-limit/ReturnSkipLimit1.feature",
        scenario="[3] SKIP with an expression that does not depend on variables",
        cypher="MATCH (n)\nWITH n SKIP toInteger(rand()*9)\nWITH count(*) AS count\nRETURN count > 0 AS nonEmpty",
        graph=GraphFixture(
            nodes=[{"id": f"n{i}", "labels": [], "nr": i} for i in range(1, 11)],
            edges=[],
        ),
        expected=Expected(
            rows=[
                {"nonEmpty": "true"},
            ],
        ),
        gfql=plan(
            match(n(name="n")),
            rows(table="nodes", source="n"),
            step("with", items=(("n", "n"),)),
            skip("toInteger(rand() * 9)"),
            step("with", items=(("count", "count(*)"),)),
            select([("nonEmpty", "count > 0")]),
        ),
        status="xfail",
        reason="WITH pipelines, SKIP, and functions are not supported",
        tags=("return", "skip", "with", "function", "xfail"),
    ),

    Scenario(
        key="return-skip-limit1-4",
        feature_path="tck/features/clauses/return-skip-limit/ReturnSkipLimit1.feature",
        scenario="[4] Accept skip zero",
        cypher="MATCH (n)\nWHERE 1 = 0\nRETURN n\nSKIP 0",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(rows=[]),
        gfql=plan(
            match(n(name="n")),
            rows(table="nodes", source="n"),
            step("where", expr="1 = 0"),
            select([("n", "n")]),
            skip(0),
        ),
        status="xfail",
        reason="SKIP is not supported",
        tags=("return", "skip", "xfail"),
    ),

    Scenario(
        key="return-skip-limit1-5",
        feature_path="tck/features/clauses/return-skip-limit/ReturnSkipLimit1.feature",
        scenario="[5] SKIP with an expression that depends on variables should fail",
        cypher="MATCH (n)\nRETURN n\nSKIP n.count",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(),
        gfql=plan(
            match(n(name="n")),
            rows(table="nodes", source="n"),
            select([("n", "n")]),
            skip("n.count"),
            step("invalid", note="SKIP expression depends on variables"),
        ),
        status="xfail",
        reason="Compile-time validation for SKIP expressions is not enforced",
        tags=("return", "skip", "syntax-error", "xfail"),
    ),

    Scenario(
        key="return-skip-limit1-6",
        feature_path="tck/features/clauses/return-skip-limit/ReturnSkipLimit1.feature",
        scenario="[6] Negative parameter for SKIP should fail",
        cypher="MATCH (p:Person)\nRETURN p.name AS name\nSKIP $_skip",
        graph=graph_fixture_from_create(
            """
            CREATE (s:Person {name: 'Steven'}),
                   (c:Person {name: 'Craig'})
            """
        ),
        expected=Expected(),
        gfql=plan(
            match(n({"label__Person": True}, name="p")),
            rows(table="nodes", source="p"),
            select([("name", "p.name")]),
            skip("$_skip"),
            step("invalid", note="negative SKIP parameter"),
        ),
        status="xfail",
        reason="Parameter binding and runtime validation for SKIP are not supported",
        tags=("return", "skip", "params", "runtime-error", "xfail"),
    ),

    Scenario(
        key="return-skip-limit1-7",
        feature_path="tck/features/clauses/return-skip-limit/ReturnSkipLimit1.feature",
        scenario="[7] Negative SKIP should fail",
        cypher="MATCH (p:Person)\nRETURN p.name AS name\nSKIP -1",
        graph=graph_fixture_from_create(
            """
            CREATE (s:Person {name: 'Steven'}),
                   (c:Person {name: 'Craig'})
            """
        ),
        expected=Expected(),
        gfql=plan(
            match(n({"label__Person": True}, name="p")),
            rows(table="nodes", source="p"),
            select([("name", "p.name")]),
            skip(-1),
            step("invalid", note="negative SKIP"),
        ),
        status="xfail",
        reason="Compile-time validation for SKIP arguments is not enforced",
        tags=("return", "skip", "syntax-error", "xfail"),
    ),

    Scenario(
        key="return-skip-limit1-8",
        feature_path="tck/features/clauses/return-skip-limit/ReturnSkipLimit1.feature",
        scenario="[8] Floating point parameter for SKIP should fail",
        cypher="MATCH (p:Person)\nRETURN p.name AS name\nSKIP $_limit",
        graph=graph_fixture_from_create(
            """
            CREATE (s:Person {name: 'Steven'}),
                   (c:Person {name: 'Craig'})
            """
        ),
        expected=Expected(),
        gfql=plan(
            match(n({"label__Person": True}, name="p")),
            rows(table="nodes", source="p"),
            select([("name", "p.name")]),
            skip("$_limit"),
            step("invalid", note="non-integer SKIP parameter"),
        ),
        status="xfail",
        reason="Parameter binding and runtime validation for SKIP are not supported",
        tags=("return", "skip", "params", "runtime-error", "xfail"),
    ),

    Scenario(
        key="return-skip-limit1-9",
        feature_path="tck/features/clauses/return-skip-limit/ReturnSkipLimit1.feature",
        scenario="[9] Floating point SKIP should fail",
        cypher="MATCH (p:Person)\nRETURN p.name AS name\nSKIP 1.5",
        graph=graph_fixture_from_create(
            """
            CREATE (s:Person {name: 'Steven'}),
                   (c:Person {name: 'Craig'})
            """
        ),
        expected=Expected(),
        gfql=plan(
            match(n({"label__Person": True}, name="p")),
            rows(table="nodes", source="p"),
            select([("name", "p.name")]),
            skip(1.5),
            step("invalid", note="non-integer SKIP literal"),
        ),
        status="xfail",
        reason="Compile-time validation for SKIP arguments is not enforced",
        tags=("return", "skip", "syntax-error", "xfail"),
    ),

    Scenario(
        key="return-skip-limit1-10",
        feature_path="tck/features/clauses/return-skip-limit/ReturnSkipLimit1.feature",
        scenario="[10] Fail when using non-constants in SKIP",
        cypher="MATCH (n)\nRETURN n\nSKIP n.count",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(),
        gfql=plan(
            match(n(name="n")),
            rows(table="nodes", source="n"),
            select([("n", "n")]),
            skip("n.count"),
            step("invalid", note="SKIP expression depends on variables"),
        ),
        status="xfail",
        reason="Compile-time validation for SKIP expressions is not enforced",
        tags=("return", "skip", "syntax-error", "xfail"),
    ),

    Scenario(
        key="return-skip-limit1-11",
        feature_path="tck/features/clauses/return-skip-limit/ReturnSkipLimit1.feature",
        scenario="[11] Fail when using negative value in SKIP",
        cypher="MATCH (n)\nRETURN n\nSKIP -1",
        graph=GraphFixture(nodes=[], edges=[]),
        expected=Expected(),
        gfql=plan(
            match(n(name="n")),
            rows(table="nodes", source="n"),
            select([("n", "n")]),
            skip(-1),
            step("invalid", note="negative SKIP"),
        ),
        status="xfail",
        reason="Compile-time validation for SKIP arguments is not enforced",
        tags=("return", "skip", "syntax-error", "xfail"),
    ),
]
