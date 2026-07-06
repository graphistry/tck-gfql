from __future__ import annotations

from tests.cypher_tck.models import Expected, GraphFixture, Scenario

FEATURE_PATH = "first_party/features/local_cypher/networkx/NetworkX.feature"
BASE_TAGS = ("first-party", "local-cypher", "networkx", "cypher-string", "cypher-string-pure")
ERROR_TAGS = (*BASE_TAGS, "cypher-string-error")

NETWORKX_PATH_GRAPH = GraphFixture(
    nodes=[
        {"id": "a"},
        {"id": "b"},
        {"id": "c"},
        {"id": "z"},
    ],
    edges=[
        {"src": "a", "dst": "b", "edge_id": "ab", "type": "LINK"},
        {"src": "b", "dst": "c", "edge_id": "bc", "type": "LINK"},
    ],
)


# HITS scores come from a scipy ``svds`` singular vector, so components near
# zero (isolated / sink / source nodes) are only defined up to sign and float
# precision — an isolated node yields NaN and near-zero scores flip to tiny
# negatives (~-1e-16). That makes both a degenerate graph and a ``>= 0`` check
# non-deterministic. HITS therefore uses a connected, non-degenerate fixture
# (every node participates; not a pure cycle) and asserts the columns are
# surfaced (``IS NOT NULL``) rather than sign-checking svds noise.
NETWORKX_HITS_GRAPH = GraphFixture(
    nodes=[{"id": "a"}, {"id": "b"}, {"id": "c"}, {"id": "z"}],
    edges=[
        {"src": "a", "dst": "b", "edge_id": "ab", "type": "LINK"},
        {"src": "a", "dst": "c", "edge_id": "ac", "type": "LINK"},
        {"src": "b", "dst": "c", "edge_id": "bc", "type": "LINK"},
        {"src": "c", "dst": "z", "edge_id": "cz", "type": "LINK"},
    ],
)


def _networkx_row_scenario(
    *,
    key: str,
    scenario: str,
    cypher: str,
    rows: list[dict[str, object]],
    graph: GraphFixture = NETWORKX_PATH_GRAPH,
) -> Scenario:
    return Scenario(
        key=key,
        feature_path=FEATURE_PATH,
        scenario=scenario,
        cypher=cypher,
        graph=graph,
        expected=Expected(rows=rows, ordered=True),
        gfql=None,
        status="supported",
        tags=BASE_TAGS,
    )


def _networkx_error_scenario(
    *,
    key: str,
    algorithm: str,
) -> Scenario:
    procedure = f"graphistry.nx.{algorithm}"
    return Scenario(
        key=key,
        feature_path=FEATURE_PATH,
        scenario=f"Reject unsupported parameters for {procedure}",
        cypher=f"CALL {procedure}({{bogus_option: 1}})",
        graph=NETWORKX_PATH_GRAPH,
        expected=Expected(rows=None),
        gfql=None,
        status="supported",
        tags=ERROR_TAGS,
    )


SCENARIOS = [
    _networkx_row_scenario(
        key="firstparty-networkx-degree-centrality-1",
        scenario="Rank a path graph by NetworkX degree centrality",
        cypher=(
            "CALL graphistry.nx.degree_centrality() "
            "YIELD nodeId, degree_centrality "
            "RETURN nodeId, degree_centrality "
            "ORDER BY degree_centrality DESC, nodeId ASC "
            "LIMIT 1"
        ),
        rows=[{"nodeId": "b", "degree_centrality": 0.6666666666666666}],
    ),
    _networkx_row_scenario(
        key="firstparty-networkx-closeness-centrality-1",
        scenario="Rank a path graph by NetworkX closeness centrality",
        cypher=(
            "CALL graphistry.nx.closeness_centrality({directed: false}) "
            "YIELD nodeId, closeness_centrality "
            "RETURN nodeId "
            "ORDER BY closeness_centrality DESC, nodeId ASC "
            "LIMIT 1"
        ),
        rows=[{"nodeId": "b"}],
    ),
    _networkx_row_scenario(
        key="firstparty-networkx-eigenvector-centrality-1",
        scenario="Rank a path graph by NetworkX eigenvector centrality",
        cypher=(
            "CALL graphistry.nx.eigenvector_centrality({directed: false, max_iter: 1000}) "
            "YIELD nodeId, eigenvector_centrality "
            "RETURN nodeId "
            "ORDER BY eigenvector_centrality DESC, nodeId ASC "
            "LIMIT 1"
        ),
        rows=[{"nodeId": "b"}],
    ),
    _networkx_row_scenario(
        key="firstparty-networkx-katz-centrality-1",
        scenario="Rank a path graph by NetworkX Katz centrality",
        cypher=(
            "CALL graphistry.nx.katz_centrality({directed: false, alpha: 0.1}) "
            "YIELD nodeId, katz_centrality "
            "RETURN nodeId "
            "ORDER BY katz_centrality DESC, nodeId ASC "
            "LIMIT 1"
        ),
        rows=[{"nodeId": "b"}],
    ),
    _networkx_row_scenario(
        key="firstparty-networkx-connected-components-1",
        scenario="Label weak components with NetworkX connected components",
        cypher=(
            "CALL graphistry.nx.connected_components({directed: false}) "
            "YIELD nodeId, labels "
            "RETURN nodeId, labels "
            "ORDER BY nodeId ASC"
        ),
        rows=[
            {"nodeId": "a", "labels": 0},
            {"nodeId": "b", "labels": 0},
            {"nodeId": "c", "labels": 0},
            {"nodeId": "z", "labels": 1},
        ],
    ),
    _networkx_row_scenario(
        key="firstparty-networkx-strongly-connected-components-1",
        scenario="Surface NetworkX strongly connected component labels",
        cypher=(
            "CALL graphistry.nx.strongly_connected_components() "
            "YIELD nodeId, labels "
            "RETURN nodeId, labels >= 0 AS has_label "
            "ORDER BY nodeId ASC"
        ),
        rows=[
            {"nodeId": "a", "has_label": True},
            {"nodeId": "b", "has_label": True},
            {"nodeId": "c", "has_label": True},
            {"nodeId": "z", "has_label": True},
        ],
    ),
    _networkx_row_scenario(
        key="firstparty-networkx-core-number-1",
        scenario="Compute NetworkX core numbers for a path plus isolate graph",
        cypher=(
            "CALL graphistry.nx.core_number() "
            "YIELD nodeId, core_number "
            "RETURN nodeId, core_number "
            "ORDER BY nodeId ASC"
        ),
        rows=[
            {"nodeId": "a", "core_number": 1},
            {"nodeId": "b", "core_number": 1},
            {"nodeId": "c", "core_number": 1},
            {"nodeId": "z", "core_number": 0},
        ],
    ),
    _networkx_row_scenario(
        key="firstparty-networkx-hits-1",
        scenario="Surface NetworkX HITS hub and authority columns",
        cypher=(
            "CALL graphistry.nx.hits() "
            "YIELD nodeId, hubs, authorities "
            "RETURN nodeId, hubs IS NOT NULL AS hub, authorities IS NOT NULL AS auth "
            "ORDER BY nodeId ASC"
        ),
        rows=[
            {"nodeId": "a", "hub": True, "auth": True},
            {"nodeId": "b", "hub": True, "auth": True},
            {"nodeId": "c", "hub": True, "auth": True},
            {"nodeId": "z", "hub": True, "auth": True},
        ],
        graph=NETWORKX_HITS_GRAPH,
    ),
    Scenario(
        key="firstparty-networkx-hits-write-1",
        feature_path=FEATURE_PATH,
        scenario="Write NetworkX HITS scores back to graph node properties",
        cypher="CALL graphistry.nx.hits.write()",
        graph=NETWORKX_PATH_GRAPH,
        expected=Expected(node_ids=("a", "b", "c", "z"), edge_ids=("ab", "bc")),
        gfql=None,
        status="supported",
        tags=BASE_TAGS,
    ),
    _networkx_error_scenario(
        key="firstparty-networkx-degree-centrality-error-1",
        algorithm="degree_centrality",
    ),
    _networkx_error_scenario(
        key="firstparty-networkx-closeness-centrality-error-1",
        algorithm="closeness_centrality",
    ),
    _networkx_error_scenario(
        key="firstparty-networkx-eigenvector-centrality-error-1",
        algorithm="eigenvector_centrality",
    ),
    _networkx_error_scenario(
        key="firstparty-networkx-katz-centrality-error-1",
        algorithm="katz_centrality",
    ),
    _networkx_error_scenario(
        key="firstparty-networkx-connected-components-error-1",
        algorithm="connected_components",
    ),
    _networkx_error_scenario(
        key="firstparty-networkx-strongly-connected-components-error-1",
        algorithm="strongly_connected_components",
    ),
    _networkx_error_scenario(
        key="firstparty-networkx-core-number-error-1",
        algorithm="core_number",
    ),
    _networkx_error_scenario(
        key="firstparty-networkx-hits-error-1",
        algorithm="hits",
    ),
]
