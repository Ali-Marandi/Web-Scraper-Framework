"""
Graph Theory / Complex Network Analysis Module for Web Link Structures.

Provides graph construction, centrality analysis, community detection,
web-specific structural analysis, and systemic-risk/failure-propagation modelling.

Only depends on the Python standard library and numpy.
"""

from __future__ import annotations

from collections import deque, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, Hashable, Iterable, List, Optional, Set, Tuple

import numpy as np


# ---- Directed Graph (adjacency-list) ---------------------------------------- #

class DiGraph:
    """Lightweight directed graph backed by adjacency-lists.

    Nodes must be hashable (URLs are strings, so this is natural).
    """

    def __init__(self) -> None:
        self._out: Dict[Hashable, Set[Hashable]] = defaultdict(set)
        self._in: Dict[Hashable, Set[Hashable]] = defaultdict(set)
        self._nodes: Set[Hashable] = set()

    def add_node(self, node: Hashable) -> None:
        """Register *node* if not already present."""
        self._nodes.add(node)

    def add_edge(self, source: Hashable, target: Hashable) -> None:
        """Add a directed edge *source* → *target*, creating nodes as needed."""
        self._nodes.add(source)
        self._nodes.add(target)
        self._out[source].add(target)
        self._in[target].add(source)

    def nodes(self) -> Set[Hashable]:
        """Return the set of all nodes."""
        return set(self._nodes)

    def edges(self) -> List[Tuple[Hashable, Hashable]]:
        """Return every directed edge as (source, target) tuples."""
        return [(s, t) for s, ts in self._out.items() for t in ts]

    def get_neighbors(self, node: Hashable) -> Set[Hashable]:
        """Out-neighbours of *node*."""
        return set(self._out.get(node, set()))

    def get_in_neighbors(self, node: Hashable) -> Set[Hashable]:
        """In-neighbours of *node*."""
        return set(self._in.get(node, set()))

    def get_out_degree(self, node: Hashable) -> int:
        """Number of outgoing edges from *node*."""
        return len(self._out.get(node, set()))

    def get_in_degree(self, node: Hashable) -> int:
        """Number of incoming edges to *node*."""
        return len(self._in.get(node, set()))

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return sum(len(tgts) for tgts in self._out.values())


# ---- Centrality Analyzer ------------------------------------------------- #

class CentralityAnalyzer:
    """Static methods that compute various centrality scores from scratch.

    Every public method accepts *nodes* (iterable of hashable) and *edges*
    (iterable of (src, tgt) tuples) so that no DiGraph instance is required.
    """

    @staticmethod
    def degree_centrality(
        nodes: Iterable[Hashable], edges: Iterable[Tuple[Hashable, Hashable]]
    ) -> Dict[Hashable, float]:
        """Normalised out-degree centrality for every node.

        score(v) = out_degree(v) / (n − 1)
        """
        node_list = list(nodes)
        n = len(node_list)
        if n <= 1:
            return {nd: 0.0 for nd in node_list}
        out_deg: Dict[Hashable, int] = defaultdict(int)
        for src, _ in edges:
            out_deg[src] += 1
        return {nd: out_deg.get(nd, 0) / (n - 1) for nd in node_list}

    @staticmethod
    def closeness_centrality(
        nodes: Iterable[Hashable], edges: Iterable[Tuple[Hashable, Hashable]]
    ) -> Dict[Hashable, float]:
        """Undirected closeness:  C(v) = (|R(v)| − 1) / Σ d(v, u),  u ∈ R(v).

        R(v) is the set of nodes reachable from *v* via BFS on the
        undirected projection of the link graph.
        """
        node_set: Set[Hashable] = set(nodes)
        adj: Dict[Hashable, Set[Hashable]] = defaultdict(set)
        for u, v in edges:
            adj[u].add(v)
            adj[v].add(u)
        result: Dict[Hashable, float] = {}
        for start in node_set:
            dist: Dict[Hashable, int] = {start: 0}
            queue: deque[Hashable] = deque([start])
            while queue:
                cur = queue.popleft()
                for nb in adj.get(cur, set()):
                    if nb not in dist:
                        dist[nb] = dist[cur] + 1
                        queue.append(nb)
            reachable = len(dist) - 1
            if reachable == 0:
                result[start] = 0.0
            else:
                total = sum(dist.values())
                result[start] = reachable / total
        return result

    @staticmethod
    def pagerank(
        nodes: Iterable[Hashable],
        edges: Iterable[Tuple[Hashable, Hashable]],
        damping: float = 0.85,
        iterations: int = 100,
    ) -> Dict[Hashable, float]:
        """Iterative PageRank on the directed link graph.

        PR(v) = (1 − d)/N + d · Σ_{u→v} PR(u) / out_deg(u)
        """
        node_list = list(nodes)
        n = len(node_list)
        if n == 0:
            return {}
        out_deg: Dict[Hashable, int] = defaultdict(int)
        in_map: Dict[Hashable, List[Hashable]] = defaultdict(list)
        for src, tgt in edges:
            out_deg[src] += 1
            in_map[tgt].append(src)
        pr = np.ones(n, dtype=np.float64) / n
        idx = {nd: i for i, nd in enumerate(node_list)}
        out_arr = np.array([out_deg.get(nd, 0) for nd in node_list], dtype=np.float64)
        dangling_mask = out_arr == 0
        out_arr[dangling_mask] = 1.0  # avoid div-by-zero; redistributed below
        for _ in range(iterations):
            dangling_sum = np.sum(pr[dangling_mask])
            new_pr = np.full(n, (1.0 - damping + damping * dangling_sum) / n, dtype=np.float64)
            for tgt, sources in in_map.items():
                for src in sources:
                    new_pr[idx[tgt]] += damping * pr[idx[src]] / out_arr[idx[src]]
            pr = new_pr
        return {nd: float(pr[idx[nd]]) for nd in node_list}

    @staticmethod
    def betweenness_centrality(
        nodes: Iterable[Hashable], edges: Iterable[Tuple[Hashable, Hashable]]
    ) -> Dict[Hashable, float]:
        """Brandes' algorithm (simplified, undirected projection).

        Returns raw betweenness scores (not normalised by pair count).
        """
        node_set: Set[Hashable] = set(nodes)
        adj: Dict[Hashable, Set[Hashable]] = defaultdict(set)
        for u, v in edges:
            adj[u].add(v)
            adj[v].add(u)
        cb: Dict[Hashable, float] = {nd: 0.0 for nd in node_set}
        for s in node_set:
            # single-source shortest-paths (BFS)
            stack: List[Hashable] = []
            pred: Dict[Hashable, List[Hashable]] = {w: [] for w in node_set}
            sigma: Dict[Hashable, int] = {s: 1}
            dist: Dict[Hashable, int] = {s: 0}
            queue: deque[Hashable] = deque([s])
            while queue:
                v = queue.popleft()
                stack.append(v)
                for w in adj.get(v, set()):
                    if w not in dist:
                        dist[w] = dist[v] + 1
                        queue.append(w)
                    if dist.get(w, -1) == dist[v] + 1:
                        sigma[w] = sigma.get(w, 0) + sigma[v]
                        pred[w].append(v)
            # accumulation
            delta: Dict[Hashable, float] = {w: 0.0 for w in node_set}
            while stack:
                w = stack.pop()
                for v in pred[w]:
                    delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w])
                if w != s:
                    cb[w] += delta[w]
        return cb

    @staticmethod
    def hubs_authorities(
        nodes: Iterable[Hashable],
        edges: Iterable[Tuple[Hashable, Hashable]],
        iterations: int = 20,
    ) -> Tuple[Dict[Hashable, float], Dict[Hashable, float]]:
        """HITS algorithm.

        Returns (hubs, authorities) dicts.  Hubs link *to* many good
        authorities; authorities are linked *from* many good hubs.
        """
        node_list = list(nodes)
        n = len(node_list)
        if n == 0:
            return {}, {}
        out_map: Dict[Hashable, List[Hashable]] = defaultdict(list)
        in_map: Dict[Hashable, List[Hashable]] = defaultdict(list)
        for src, tgt in edges:
            out_map[src].append(tgt)
            in_map[tgt].append(src)
        idx = {nd: i for i, nd in enumerate(node_list)}
        hubs = np.ones(n, dtype=np.float64)
        auths = np.ones(n, dtype=np.float64)
        for _ in range(iterations):
            # authority update
            new_auths = np.zeros(n, dtype=np.float64)
            for tgt, sources in in_map.items():
                for src in sources:
                    new_auths[idx[tgt]] += hubs[idx[src]]
            # hub update
            new_hubs = np.zeros(n, dtype=np.float64)
            for src, targets in out_map.items():
                for tgt in targets:
                    new_hubs[idx[src]] += auths[idx[tgt]]
            # normalise
            a_norm = np.linalg.norm(new_auths) or 1.0
            h_norm = np.linalg.norm(new_hubs) or 1.0
            auths = new_auths / a_norm
            hubs = new_hubs / h_norm
        return (
            {nd: float(hubs[idx[nd]]) for nd in node_list},
            {nd: float(auths[idx[nd]]) for nd in node_list},
        )


# ---- Community Detector -------------------------------------------------- #

class CommunityDetector:
    """Graph partitioning algorithms operating on undirected projections."""

    @staticmethod
    def _undirected_adj(
        nodes: Iterable[Hashable], edges: Iterable[Tuple[Hashable, Hashable]]
    ) -> Tuple[Set[Hashable], Dict[Hashable, Set[Hashable]]]:
        node_set = set(nodes)
        adj: Dict[Hashable, Set[Hashable]] = defaultdict(set)
        for u, v in edges:
            if u in node_set and v in node_set:
                adj[u].add(v)
                adj[v].add(u)
        return node_set, adj

    @staticmethod
    def connected_components(
        nodes: Iterable[Hashable], edges: Iterable[Tuple[Hashable, Hashable]]
    ) -> List[Set[Hashable]]:
        """Return a list of connected components (sets of nodes)."""
        node_set, adj = CommunityDetector._undirected_adj(nodes, edges)
        visited: Set[Hashable] = set()
        components: List[Set[Hashable]] = []
        for nd in node_set:
            if nd in visited:
                continue
            comp: Set[Hashable] = set()
            queue: deque[Hashable] = deque([nd])
            while queue:
                cur = queue.popleft()
                if cur in visited:
                    continue
                visited.add(cur)
                comp.add(cur)
                for nb in adj.get(cur, set()):
                    if nb not in visited:
                        queue.append(nb)
            components.append(comp)
        return components

    @staticmethod
    def find_bridges(
        nodes: Iterable[Hashable], edges: Iterable[Tuple[Hashable, Hashable]]
    ) -> List[Tuple[Hashable, Hashable]]:
        """Tarjan's bridge-finding algorithm (undirected graph).

        Returns edges whose removal would increase the number of connected
        components.
        """
        node_set, adj = CommunityDetector._undirected_adj(nodes, edges)
        bridges: List[Tuple[Hashable, Hashable]] = []
        disc: Dict[Hashable, int] = {}
        low: Dict[Hashable, int] = {}
        timer = [0]

        def dfs(u: Hashable, parent: Optional[Hashable]) -> None:
            disc[u] = low[u] = timer[0]
            timer[0] += 1
            for v in adj.get(u, set()):
                if v not in disc:
                    dfs(v, u)
                    low[u] = min(low[u], low[v])
                    if low[v] > disc[u]:
                        bridges.append((u, v))
                elif v != parent:
                    low[u] = min(low[u], disc[v])

        for nd in node_set:
            if nd not in disc:
                dfs(nd, None)
        return bridges

    @staticmethod
    def detect_communities_louvain_like(
        nodes: Iterable[Hashable],
        edges: Iterable[Tuple[Hashable, Hashable]],
    ) -> List[Set[Hashable]]:
        """Simplified Louvain-style modularity optimisation.

        Repeatedly moves each node to the neighbouring community that yields
        the greatest modularity gain, stopping when no improvement is found.
        """
        node_list = list(nodes)
        n = len(node_list)
        if n == 0:
            return []
        node_set, adj = CommunityDetector._undirected_adj(node_list, edges)
        m = sum(len(nb) for nb in adj.values()) / 2.0  # undirected edge count
        if m == 0:
            return [set(node_list)]
        # degrees (undirected)
        deg: Dict[Hashable, int] = {nd: len(adj.get(nd, set())) for nd in node_set}

        # initialise: every node in its own community
        community: Dict[Hashable, int] = {nd: i for i, nd in enumerate(node_list)}

        def _modularity() -> float:
            com_sets: Dict[int, List[Hashable]] = defaultdict(list)
            for nd, c in community.items():
                com_sets[c].append(nd)
            q = 0.0
            for c, members in com_sets.items():
                l_c = 0
                for u in members:
                    for v in adj.get(u, set()):
                        if community.get(v) == c:
                            l_c += 1
                l_c /= 2.0
                d_c = sum(deg[u] for u in members)
                q += l_c / m - (d_c / (2.0 * m)) ** 2
            return q

        improved = True
        while improved:
            improved = False
            for nd in node_list:
                best_c = community[nd]
                best_gain = 0.0
                current_c = community[nd]
                neighbour_coms: Set[int] = {community[nb] for nb in adj.get(nd, set())}
                for c in neighbour_coms:
                    if c == current_c:
                        continue
                    community[nd] = c
                    new_q = _modularity()
                    community[nd] = current_c
                    old_q = _modularity() if best_gain != 0.0 else new_q  # first eval
                    gain = new_q - old_q if best_gain != 0.0 else 0.0
                    if c == list(neighbour_coms)[0]:
                        baseline = _modularity()
                        community[nd] = c
                        gain = _modularity() - baseline
                        community[nd] = current_c
                    if gain > best_gain:
                        best_gain = gain
                        best_c = c
                if best_c != current_c:
                    community[nd] = best_c
                    improved = True
        # collect communities
        com_map: Dict[int, Set[Hashable]] = defaultdict(set)
        for nd, c in community.items():
            com_map[c].add(nd)
        return list(com_map.values())


# ---- Risk Propagator (Contagion / Systemic Risk) ------------------------- #

class RiskPropagator:
    """Model failure cascades through a directed link graph.

    Each node has a *health* in [0, 1].  A node fails when the fraction
    of its in-neighbours that have failed exceeds *threshold*.
    """

    @staticmethod
    def simulate_failure(
        nodes: Iterable[Hashable],
        edges: Iterable[Tuple[Hashable, Hashable]],
        initial_failed: Iterable[Hashable],
        threshold: float = 0.3,
    ) -> Dict[Hashable, int]:
        """Return a mapping node → round-in-which-it-failed (0 = initial).

        Nodes that never fail are absent from the result.
        """
        node_set = set(nodes)
        in_map: Dict[Hashable, List[Hashable]] = defaultdict(list)
        for u, v in edges:
            in_map[v].append(u)
        failed: Dict[Hashable, int] = {nd: 0 for nd in initial_failed if nd in node_set}
        failed_set = set(failed)
        round_num = 1
        changed = True
        while changed:
            changed = False
            newly_failed: Set[Hashable] = set()
            for nd in node_set - failed_set:
                neighbours = in_map.get(nd, [])
                if not neighbours:
                    continue
                fail_count = sum(1 for nb in neighbours if nb in failed_set)
                if fail_count / len(neighbours) >= threshold:
                    newly_failed.add(nd)
            if newly_failed:
                changed = True
                for nd in newly_failed:
                    failed[nd] = round_num
                failed_set |= newly_failed
                round_num += 1
        return failed

    @staticmethod
    def calculate_systemic_risk(
        nodes: Iterable[Hashable],
        edges: Iterable[Tuple[Hashable, Hashable]],
    ) -> float:
        """Estimate structural vulnerability ∈ [0, 1].

        For each node as a single seed failure, compute the cascade size
        and average over all nodes.  The ratio of the mean cascade size
        to the total node count is the systemic-risk score.
        """
        node_list = list(nodes)
        n = len(node_list)
        if n == 0:
            return 0.0
        total_cascade = 0
        for nd in node_list:
            cascade = RiskPropagator.simulate_failure(node_list, edges, [nd])
            total_cascade += len(cascade)
        return (total_cascade / n) / n


# ---- Web Analysis Report ------------------------------------------------ #

@dataclass
class WebAnalysisReport:
    """Aggregated result of a full site-structure analysis."""
    total_pages: int = 0
    total_links: int = 0
    density: float = 0.0
    avg_degree: float = 0.0
    clustering_coefficient: float = 0.0
    hub_pages: List[Tuple[str, float]] = field(default_factory=list)
    authority_pages: List[Tuple[str, float]] = field(default_factory=list)
    orphan_pages: List[str] = field(default_factory=list)
    dead_ends: List[str] = field(default_factory=list)
    communities: List[Set[str]] = field(default_factory=list)
    max_depth: int = 0
    connectivity_score: float = 0.0
    centrality_scores: Dict[str, Dict[str, float]] = field(default_factory=dict)
    systemic_risk: float = 0.0
    bridges: List[Tuple[str, str]] = field(default_factory=list)


# ---- Web Structure Analyser (main facade) -------------------------------- #

class WebStructureAnalyzer:
    """High-level facade that builds a graph from URL-explorer results
    and produces a comprehensive :class:`WebAnalysisReport`.
    """

    def __init__(self) -> None:
        self._graph = DiGraph()
        self._base_url: str = ""

    # -- graph construction ------------------------------------------------ #

    def build_from_explorer_result(self, explorer_result: Any) -> DiGraph:
        """Populate the internal graph from an ExplorerResult (internal links only)."""
        from urllib.parse import urlparse

        self._graph = DiGraph()
        self._base_url = getattr(explorer_result, "base_url", "") or ""
        base_origin = urlparse(self._base_url).netloc if self._base_url else ""

        links = getattr(explorer_result, "links", []) or []
        for link_info in links:
            source = getattr(link_info, "source_url", "") or ""
            target = getattr(link_info, "url", "") or ""
            cat = getattr(link_info, "category", None)
            cat_val = cat.value if hasattr(cat, "value") else str(cat)
            if cat_val != "internal":
                continue
            # ensure same origin
            if base_origin and urlparse(target).netloc != base_origin:
                continue
            self._graph.add_edge(source, target)

        # ensure nodes that were only targets are also added
        for link_info in links:
            target = getattr(link_info, "url", "") or ""
            self._graph.add_node(target)
        return self._graph

    # -- individual analyses ------------------------------------------------ #

    def find_orphan_pages(self) -> List[str]:
        """Pages with no inbound links, excluding the base URL."""
        orphans: List[str] = []
        for nd in self._graph.nodes():
            if nd == self._base_url:
                continue
            if self._graph.get_in_degree(nd) == 0:
                orphans.append(nd)
        return sorted(orphans)

    def find_dead_ends(self) -> List[str]:
        """Pages with **no** outbound links (out-degree == 0)."""
        return sorted(
            nd for nd in self._graph.nodes()
            if self._graph.get_out_degree(nd) == 0
        )

    def calculate_site_depth(self) -> int:
        """Maximum BFS depth from the base URL (0 if unreachable)."""
        if self._base_url not in self._graph.nodes():
            return 0
        visited: Dict[str, int] = {self._base_url: 0}
        queue: deque[Tuple[str, int]] = deque([(self._base_url, 0)])
        max_d = 0
        while queue:
            cur, d = queue.popleft()
            for nb in self._graph.get_neighbors(cur):
                if nb not in visited:
                    visited[nb] = d + 1
                    max_d = max(max_d, d + 1)
                    queue.append((nb, d + 1))
        return max_d

    def identify_hub_pages(self, top_n: int = 10) -> List[Tuple[str, float]]:
        """Top-N pages by authority score (most linked-to)."""
        _, auths = CentralityAnalyzer.hubs_authorities(
            self._graph.nodes(), self._graph.edges()
        )
        ranked = sorted(auths.items(), key=lambda x: x[1], reverse=True)
        return [(str(u), s) for u, s in ranked[:top_n]]

    def identify_authority_pages(self, top_n: int = 10) -> List[Tuple[str, float]]:
        """Top-N pages by hub score (link out to many others)."""
        hubs, _ = CentralityAnalyzer.hubs_authorities(
            self._graph.nodes(), self._graph.edges()
        )
        ranked = sorted(hubs.items(), key=lambda x: x[1], reverse=True)
        return [(str(u), s) for u, s in ranked[:top_n]]

    def get_site_map_hierarchy(self) -> Dict[str, Any]:
        """Tree rooted at base URL (cycles broken via per-branch visited set)."""
        root = self._base_url
        if root not in self._graph.nodes():
            return {"url": root, "children": []}

        def _build(node: str, visited: Set[str]) -> Dict[str, Any]:
            visited.add(node)
            children = []
            for nb in sorted(self._graph.get_neighbors(node)):
                if nb not in visited:
                    children.append(_build(nb, visited))
            return {"url": node, "children": children}

        return _build(root, set())

    def calculate_connectivity(self) -> Dict[str, float]:
        """Density, average degree, and global clustering coefficient."""
        n = self._graph.node_count
        m = self._graph.edge_count
        if n <= 1:
            return {"density": 0.0, "avg_degree": 0.0, "clustering_coefficient": 0.0}
        density = m / (n * (n - 1))
        total_deg = sum(self._graph.get_out_degree(nd) for nd in self._graph.nodes())
        avg_deg = total_deg / n
        # clustering coefficient (undirected projection)
        adj: Dict[Hashable, Set[Hashable]] = defaultdict(set)
        for u, v in self._graph.edges():
            adj[u].add(v)
            adj[v].add(u)
        cc_sum = 0.0
        cc_count = 0
        for nd in self._graph.nodes():
            k = len(adj.get(nd, set()))
            if k < 2:
                continue
            nbrs = adj[nd]
            triangles = sum(1 for a in nbrs for b in nbrs if a < b and b in adj.get(a, set()))
            max_tri = k * (k - 1) / 2.0
            cc_sum += (2.0 * triangles) / max_tri
            cc_count += 1
        clustering = cc_sum / cc_count if cc_count else 0.0
        return {
            "density": density,
            "avg_degree": avg_deg,
            "clustering_coefficient": clustering,
        }

    # -- full analysis ----------------------------------------------------- #

    def analyze(self, explorer_result: Any) -> WebAnalysisReport:
        """Run the complete analysis pipeline and return a report."""
        self.build_from_explorer_result(explorer_result)
        nodes = self._graph.nodes()
        edges = self._graph.edges()
        conn = self.calculate_connectivity()

        hubs_scores, auth_scores = CentralityAnalyzer.hubs_authorities(nodes, edges)
        pr_scores = CentralityAnalyzer.pagerank(nodes, edges)
        cc_scores = CentralityAnalyzer.closeness_centrality(nodes, edges)
        bc_scores = CentralityAnalyzer.betweenness_centrality(nodes, edges)
        dc_scores = CentralityAnalyzer.degree_centrality(nodes, edges)

        centrality: Dict[str, Dict[str, float]] = {}
        for nd in nodes:
            nd_str = str(nd)
            centrality[nd_str] = {
                "pagerank": pr_scores.get(nd, 0.0),
                "closeness": cc_scores.get(nd, 0.0),
                "betweenness": bc_scores.get(nd, 0.0),
                "degree": dc_scores.get(nd, 0.0),
                "hub": hubs_scores.get(nd, 0.0),
                "authority": auth_scores.get(nd, 0.0),
            }

        communities = CommunityDetector.detect_communities_louvain_like(nodes, edges)
        bridges = CommunityDetector.find_bridges(nodes, edges)
        components = CommunityDetector.connected_components(nodes, edges)

        # connectivity score: fraction of nodes in the largest component
        largest = max((len(c) for c in components), default=0)
        conn_score = largest / self._graph.node_count if self._graph.node_count else 0.0

        sys_risk = RiskPropagator.calculate_systemic_risk(nodes, edges)

        return WebAnalysisReport(
            total_pages=self._graph.node_count,
            total_links=self._graph.edge_count,
            density=conn["density"],
            avg_degree=conn["avg_degree"],
            clustering_coefficient=conn["clustering_coefficient"],
            hub_pages=self.identify_hub_pages(),
            authority_pages=self.identify_authority_pages(),
            orphan_pages=self.find_orphan_pages(),
            dead_ends=self.find_dead_ends(),
            communities=[{str(n) for n in c} for c in communities],
            max_depth=self.calculate_site_depth(),
            connectivity_score=conn_score,
            centrality_scores=centrality,
            systemic_risk=sys_risk,
            bridges=[(str(u), str(v)) for u, v in bridges],
        )
