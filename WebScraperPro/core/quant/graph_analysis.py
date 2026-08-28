"""
graph_analysis.py — Graph Theory & Complex Network Analysis for Quantitative Finance

Implements correlation networks, minimum spanning trees, spectral community detection,
all four classical centrality measures from scratch, systemic-risk shock propagation,
threshold/SIR/DebtRank contagion models, partial-correlation graphs, a simplified
PC causal-discovery algorithm, and DAG topological sorting.

Dependencies: numpy, pandas, scipy only.  No networkx.
"""

from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats


# --------------------------------------------------------------------------- #
#  1. CorrelationNetwork                                                       #
# --------------------------------------------------------------------------- #


class CorrelationNetwork:
    """Build and analyse correlation-based financial networks.

    Every public method returns a plain ``dict`` with structured results so
    callers never need to touch raw arrays unless they want to.
    """

    def __init__(self):
        pass

    # ---- construction ------------------------------------------------------ #

    def build_correlation_network(self, returns_matrix, threshold=0.3):
        """Build an unweighted adjacency matrix from a returns correlation matrix.

        Parameters
        ----------
        returns_matrix : array-like, shape (T, N)
            Asset returns — each column is a time-series for one node.
        threshold : float
            Edges are kept when ``|corr(i, j)| > threshold``.

        Returns
        -------
        dict with keys: adjacency, correlation_matrix, edge_list, node_names
        """
        returns = np.asarray(returns_matrix, dtype=float)
        if returns.ndim == 1:
            returns = returns.reshape(-1, 1)

        n = returns.shape[1]
        corr = np.corrcoef(returns, rowvar=False)
        np.fill_diagonal(corr, 0.0)

        adjacency = np.where(np.abs(corr) > threshold, 1.0, 0.0)
        adjacency = np.maximum(adjacency, adjacency.T)  # enforce symmetry

        edges = [
            (i, j, float(corr[i, j]))
            for i in range(n)
            for j in range(i + 1, n)
            if adjacency[i, j] > 0
        ]

        node_names = (
            list(returns_matrix.columns)
            if hasattr(returns_matrix, "columns")
            else list(range(n))
        )

        return {
            "adjacency": adjacency,
            "correlation_matrix": corr,
            "edge_list": edges,
            "node_names": node_names,
        }

    # ---- MST ---------------------------------------------------------------- #

    def minimum_spanning_tree(self, returns_matrix):
        """Minimum spanning tree via Prim's algorithm on the distance matrix.

        Distance between nodes *i* and *j* is defined as ``1 - |corr(i,j)|``.

        Returns
        -------
        dict with keys: edges (list of (u, v, distance)), adjacency (N×N)
        """
        returns = np.asarray(returns_matrix, dtype=float)
        if returns.ndim == 1:
            returns = returns.reshape(-1, 1)
        n = returns.shape[1]

        corr = np.corrcoef(returns, rowvar=False)
        dist = 1.0 - np.abs(corr)
        np.fill_diagonal(dist, 0.0)

        in_mst = np.zeros(n, dtype=bool)
        in_mst[0] = True
        mst_edges = []
        mst_adj = np.zeros((n, n))

        for _ in range(n - 1):
            best_d, best_u, best_v = np.inf, -1, -1
            for i in range(n):
                if not in_mst[i]:
                    continue
                for j in range(n):
                    if not in_mst[j] and dist[i, j] < best_d:
                        best_d, best_u, best_v = dist[i, j], i, j
            if best_u < 0:
                break
            in_mst[best_v] = True
            mst_edges.append((best_u, best_v, float(best_d)))
            mst_adj[best_u, best_v] = mst_adj[best_v, best_u] = 1.0

        return {"edges": mst_edges, "adjacency": mst_adj}

    # ---- community detection ----------------------------------------------- #

    def community_detection(self, returns_matrix, n_communities=None):
        """Spectral clustering on the normalised graph Laplacian.

        If *n_communities* is ``None`` the number of clusters is chosen via
        the eigenvalue-gap heuristic (largest jump among the smallest
        eigenvalues of the Laplacian).

        Returns
        -------
        dict with keys: labels, communities, n_communities, eigenvalues
        """
        corr = np.corrcoef(np.asarray(returns_matrix, dtype=float), rowvar=False)
        n = corr.shape[0]
        np.fill_diagonal(corr, 0.0)

        W = np.abs(corr)
        d = W.sum(axis=1)
        D = np.diag(d)
        L = D - W

        # Normalised Laplacian  L̃ = D^{-1/2} L D^{-1/2}
        d_inv_sqrt = np.where(d > 0, 1.0 / np.sqrt(d), 0.0)
        L_norm = (d_inv_sqrt[:, None] * L) * d_inv_sqrt[None, :]

        eigenvalues, eigenvectors = np.linalg.eigh(L_norm)

        # --- eigenvalue gap heuristic --------------------------------------- #
        if n_communities is None:
            k_candidates = min(n - 1, 20)
            gaps = np.diff(eigenvalues[: k_candidates + 1])
            # skip the first (≈0) eigenvalue
            gap_idx = int(np.argmax(gaps[1:])) + 1
            n_communities = max(2, min(gap_idx + 1, n))

        k = min(n_communities, n - 1)
        U = eigenvectors[:, :k]

        # Row-normalise the embedding
        row_norms = np.linalg.norm(U, axis=1, keepdims=True)
        row_norms = np.where(row_norms > 1e-10, row_norms, 1.0)
        U_norm = U / row_norms

        labels = self._kmeans(U_norm, n_communities)

        communities = {
            c: sorted(int(idx) for idx in np.where(labels == c)[0])
            for c in range(n_communities)
        }

        return {
            "labels": labels,
            "communities": communities,
            "n_communities": n_communities,
            "eigenvalues": eigenvalues[:k].tolist(),
        }

    # ---- helper: k-means from scratch -------------------------------------- #

    @staticmethod
    def _kmeans(X, k, max_iter=300, n_init=20):
        """Minimal k-means (forgoing scikit-learn)."""
        n, d = X.shape
        best_labels, best_inertia = None, np.inf

        for _ in range(n_init):
            idx = np.random.choice(n, k, replace=False)
            centroids = X[idx].copy()
            for _ in range(max_iter):
                # squared distances  (n, k)
                dists = (
                    np.sum(X ** 2, axis=1, keepdims=True)
                    - 2.0 * X @ centroids.T
                    + np.sum(centroids ** 2, axis=1)
                )
                labels = np.argmin(dists, axis=1)
                new_centroids = np.empty_like(centroids)
                for j in range(k):
                    mask = labels == j
                    new_centroids[j] = (
                        X[mask].mean(axis=0) if mask.any() else centroids[j]
                    )
                if np.allclose(centroids, new_centroids, atol=1e-8):
                    break
                centroids = new_centroids
            inertia = sum(
                np.sum((X[labels == j] - centroids[j]) ** 2) for j in range(k)
            )
            if inertia < best_inertia:
                best_inertia = inertia
                best_labels = labels.copy()
        return best_labels

    # ---- centrality measures ------------------------------------------------ #

    def centrality_measures(self, adjacency):
        """Degree, betweenness, closeness, and eigenvector centrality.

        All four measures are computed from scratch (no networkx).

        Returns
        -------
        dict with keys: degree, betweenness, closeness, eigenvector
        """
        A = np.asarray(adjacency, dtype=float)
        n = A.shape[0]

        degree = A.sum(axis=1)
        max_deg = n - 1 if n > 1 else 1
        degree_cen = degree / max_deg

        betweenness_cen = self._betweenness(A, n)
        closeness_cen = self._closeness(A, n)
        eigenvector_cen = self._eigenvector(A, n)

        return {
            "degree": degree_cen,
            "betweenness": betweenness_cen,
            "closeness": closeness_cen,
            "eigenvector": eigenvector_cen,
        }

    # -- Brandes betweenness -------------------------------------------------- #

    @staticmethod
    def _betweenness(A, n):
        betweenness = np.zeros(n)
        for s in range(n):
            S = []
            P = [[] for _ in range(n)]
            sigma = np.zeros(n)
            sigma[s] = 1.0
            dist = np.full(n, -1)
            dist[s] = 0
            Q = [s]

            while Q:
                v = Q.pop(0)
                S.append(v)
                for w in np.where(A[v] > 0)[0]:
                    if dist[w] < 0:
                        Q.append(w)
                        dist[w] = dist[v] + 1
                    if dist[w] == dist[v] + 1:
                        sigma[w] += sigma[v]
                        P[w].append(v)

            delta = np.zeros(n)
            while S:
                w = S.pop()
                for v in P[w]:
                    delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w])
                if w != s:
                    betweenness[w] += delta[w]

        scale = (n - 1) * (n - 2) / 2.0
        if scale > 0:
            betweenness /= scale
        return betweenness

    # -- closeness via BFS ---------------------------------------------------- #

    @staticmethod
    def _closeness(A, n):
        closeness = np.zeros(n)
        for s in range(n):
            dist = np.full(n, -1)
            dist[s] = 0
            Q = [s]
            while Q:
                v = Q.pop(0)
                for w in np.where(A[v] > 0)[0]:
                    if dist[w] < 0:
                        dist[w] = dist[v] + 1
                        Q.append(w)
            reachable = dist[dist >= 0]
            if reachable.size > 1:
                closeness[s] = (reachable.size - 1) / reachable.sum()
        return closeness

    # -- eigenvector centrality via power iteration ---------------------------- #

    @staticmethod
    def _eigenvector(A, n, max_iter=1000, tol=1e-8):
        x = np.random.rand(n)
        x /= np.linalg.norm(x)
        for _ in range(max_iter):
            x_new = A @ x
            norm = np.linalg.norm(x_new)
            if norm < 1e-12:
                return np.zeros(n)
            x_new /= norm
            if np.abs(np.abs(x_new @ x) - 1.0) < tol:
                break
            x = x_new
        x = np.abs(x_new)
        s = x.sum()
        return x / s if s > 0 else x

    # ---- systemic risk ----------------------------------------------------- #

    def systemic_risk_score(self, adjacency, weights):
        """DebtRank-inspired per-node systemic risk via shock propagation.

        For each node *s* we inject a unit shock, then iteratively propagate
        distress through row-normalised adjacency until convergence.  The
        systemic-risk contribution of *s* is ``sum(D_i * w_i)``.

        Returns
        -------
        dict with keys: node_risk, total_systemic_risk, normalized_risk
        """
        A = np.asarray(adjacency, dtype=float)
        w = np.asarray(weights, dtype=float)
        n = A.shape[0]

        row_sums = A.sum(axis=1, keepdims=True)
        W = A / np.where(row_sums > 0, row_sums, 1.0)

        systemic_risk = np.zeros(n)

        for s in range(n):
            D = np.zeros(n)
            D[s] = 1.0

            for _ in range(n):  # at most n propagation rounds
                D_new = D.copy()
                for i in range(n):
                    if i == s:
                        continue
                    impact = (W[:, i] * w * D).sum()
                    D_new[i] = min(1.0, D[i] + (impact / w[i] if w[i] > 0 else 0.0))
                if np.allclose(D_new, D, atol=1e-12):
                    break
                D = D_new

            systemic_risk[s] = (D * w).sum()

        total = systemic_risk.sum()
        return {
            "node_risk": systemic_risk,
            "total_systemic_risk": total,
            "normalized_risk": systemic_risk / total if total > 0 else systemic_risk,
        }


# --------------------------------------------------------------------------- #
#  2. ContagionModel                                                         #
# --------------------------------------------------------------------------- #


class ContagionModel:
    """Financial contagion and systemic-risk models on networks."""

    def __init__(self):
        pass

    # ---- threshold contagion ----------------------------------------------- #

    def threshold_model(self, adjacency, initial_shocks, threshold=0.5, n_steps=20):
        """Threshold contagion: node fails if weighted failed-neighbour sum > threshold.

        Parameters
        ----------
        adjacency : (N, N) array-like
        initial_shocks : array-like of int
            Indices of initially failed nodes.
        threshold : float
        n_steps : int

        Returns
        -------
        dict with keys: cascade_sequence, final_state, n_failed,
        n_steps_taken, cascade_size_ratio
        """
        A = np.asarray(adjacency, dtype=float)
        n = A.shape[0]

        row_sums = A.sum(axis=1, keepdims=True)
        W = A / np.where(row_sums > 0, row_sums, 1.0)

        state = np.zeros(n, dtype=int)
        state[np.asarray(initial_shocks, dtype=int)] = 1
        cascade = [state.copy()]

        for _ in range(n_steps):
            new_state = state.copy()
            for i in range(n):
                if state[i] == 1:
                    continue
                if (W[i] * state).sum() > threshold:
                    new_state[i] = 1
            if np.array_equal(new_state, state):
                break
            state = new_state
            cascade.append(state.copy())

        return {
            "cascade_sequence": cascade,
            "final_state": state,
            "n_failed": int(state.sum()),
            "n_steps_taken": len(cascade) - 1,
            "cascade_size_ratio": float(state.sum() / n) if n else 0.0,
        }

    # ---- SIR epidemic model ------------------------------------------------ #

    def sir_model(
        self,
        adjacency,
        initial_infected,
        beta=0.3,
        gamma=0.1,
        n_steps=50,
    ):
        """Stochastic SIR model on a financial network.

        * S → I at effective rate that grows with the number of infected
          neighbours: ``p_infect = 1 − (1−β)^{n_inf_neighbours}``
        * I → R at rate *gamma* per step.

        Returns
        -------
        dict with keys: susceptible, infected, recovered (lists per step),
        final_state, total_ever_infected, peak_infected, n_steps
        """
        A = np.asarray(adjacency, dtype=float)
        n = A.shape[0]

        # States: 0 = Susceptible, 1 = Infected, 2 = Recovered
        state = np.zeros(n, dtype=int)
        state[np.asarray(initial_infected, dtype=int)] = 1

        s_hist, i_hist, r_hist = [], [], []

        for _ in range(n_steps):
            s_hist.append(int((state == 0).sum()))
            i_hist.append(int((state == 1).sum()))
            r_hist.append(int((state == 2).sum()))

            new_state = state.copy()
            for i in range(n):
                if state[i] == 1:
                    if np.random.random() < gamma:
                        new_state[i] = 2
                elif state[i] == 0:
                    n_inf_nbrs = int((A[i] * (state == 1).astype(float)).sum())
                    p_inf = 1.0 - (1.0 - beta) ** n_inf_nbrs
                    if np.random.random() < p_inf:
                        new_state[i] = 1
            state = new_state

            if (state == 1).sum() == 0:
                # record final steady state
                s_hist.append(int((state == 0).sum()))
                i_hist.append(0)
                r_hist.append(int((state == 2).sum()))
                break

        return {
            "susceptible": s_hist,
            "infected": i_hist,
            "recovered": r_hist,
            "final_state": state,
            "total_ever_infected": int((state != 0).sum()),
            "peak_infected": max(i_hist) if i_hist else 0,
            "n_steps": len(i_hist),
        }

    # ---- DebtRank ----------------------------------------------------------- #

    def debt_rank(self, adjacency, weights, initial_shock_node, impact_matrix=None):
        """DebtRank algorithm (Battiston et al. 2012).

        Distress propagation rule:
            ``D_i ← min(1, D_i + Σ_j W_{ji} · V_j · D_j / V_i)``
        where *W* is a column-normalised impact matrix (defaults to the
        adjacency matrix) and *V* is the node weight vector.

        Returns
        -------
        dict with keys: debt_rank, final_distress, distress_history,
        total_impact, n_affected, max_distress, mean_distress
        """
        A = np.asarray(adjacency, dtype=float)
        V = np.asarray(weights, dtype=float)
        n = A.shape[0]

        if impact_matrix is None:
            col_sums = A.sum(axis=0)
            W = A / np.where(col_sums > 0, col_sums, 1.0)
        else:
            W = np.asarray(impact_matrix, dtype=float)

        D = np.zeros(n)
        D[int(initial_shock_node)] = 1.0
        visited = np.zeros(n, dtype=bool)
        visited[int(initial_shock_node)] = True

        queue = [int(initial_shock_node)]
        history = [D.copy()]

        while queue:
            i = queue.pop(0)
            for j in range(n):
                if not visited[j] and W[i, j] > 0:
                    impact = W[i, j] * V[i] * D[i] / V[j] if V[j] > 0 else 0.0
                    new_d = min(1.0, D[j] + impact)
                    if new_d > D[j]:
                        D[j] = new_d
                        visited[j] = True
                        queue.append(j)
            history.append(D.copy())

        total = (D * V).sum()
        shock_val = V[int(initial_shock_node)] if int(initial_shock_node) < n else 0.0
        affected_mask = D > 0

        return {
            "debt_rank": float(total - shock_val),
            "final_distress": D,
            "distress_history": history,
            "total_impact": float(total),
            "n_affected": int(affected_mask.sum()),
            "max_distress": float(D.max()),
            "mean_distress": float(D[affected_mask].mean()) if affected_mask.any() else 0.0,
        }


# --------------------------------------------------------------------------- #
#  3. CausalGraph                                                            #
# --------------------------------------------------------------------------- #


class CausalGraph:
    """Causal graph inference: partial correlations, PC algorithm, DAG ordering."""

    def __init__(self):
        pass

    # ---- partial-correlation graph ----------------------------------------- #

    def build_partial_correlation_graph(self, data_matrix, threshold=0.1):
        """Partial-correlation graph from the precision matrix.

        The precision matrix ``Ω = Σ^{-1}`` encodes conditional
        independences: the partial correlation of *i* and *j* given all
        other variables is

            ``ρ(i,j|rest) = −Ω_{ij} / √(Ω_{ii} Ω_{jj})``

        An edge is kept when ``|partial_corr| > threshold``.

        Returns
        -------
        dict with keys: precision_matrix, partial_correlations, edges, adjacency
        """
        X = np.asarray(data_matrix, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        _, p = X.shape

        cov = np.cov(X, rowvar=False)
        if cov.ndim == 0:
            cov = np.array([[float(cov)]])

        cov_reg = cov + 1e-6 * np.eye(p)  # regularise for invertibility
        try:
            precision = np.linalg.inv(cov_reg)
        except np.linalg.LinAlgError:
            precision = np.linalg.pinv(cov_reg)

        diag_sqrt = np.sqrt(np.diag(precision))
        diag_sqrt = np.where(diag_sqrt > 0, diag_sqrt, 1.0)

        partial_corr = np.zeros((p, p))
        for i in range(p):
            for j in range(p):
                partial_corr[i, j] = -precision[i, j] / (diag_sqrt[i] * diag_sqrt[j])
        np.fill_diagonal(partial_corr, 0.0)

        edges, adj = [], np.zeros((p, p))
        for i in range(p):
            for j in range(i + 1, p):
                val = float(partial_corr[i, j])
                if abs(val) > threshold:
                    edges.append((i, j, val))
                    adj[i, j] = adj[j, i] = val

        return {
            "precision_matrix": precision,
            "partial_correlations": partial_corr,
            "edges": edges,
            "adjacency": adj,
        }

    # ---- simplified PC algorithm -------------------------------------------- #

    def pc_algorithm_simplified(self, data_matrix, alpha=0.05):
        """Simplified PC algorithm for causal skeleton discovery.

        1. Start with a complete undirected graph.
        2. For each adjacent pair (i, j), condition on subsets of
           increasing size drawn from the remaining neighbours.
        3. Remove the edge if the partial correlation is *not* significant
           (Fisher z-transform test at level *alpha*).

        Returns
        -------
        dict with keys: skeleton, edges, separation_sets, n_edges, n_nodes
        """
        X = np.asarray(data_matrix, dtype=float)
        n_samples, p = X.shape

        # full correlation matrix
        cov = np.cov(X, rowvar=False)
        if cov.ndim == 0:
            cov = np.array([[float(cov)]])
        std = np.sqrt(np.diag(cov))
        std = np.where(std > 0, std, 1.0)
        corr = cov / np.outer(std, std)

        # complete graph
        adj = np.ones((p, p), dtype=int)
        np.fill_diagonal(adj, 0)
        sep_set = [[set() for _ in range(p)] for _ in range(p)]

        depth = 0
        max_depth = p - 2

        while depth <= max_depth:
            edges_to_test = []
            for i in range(p):
                for j in range(i + 1, p):
                    if adj[i, j] == 1:
                        nbrs_i = [k for k in range(p) if adj[i, k] == 1 and k != j]
                        if len(nbrs_i) >= depth:
                            edges_to_test.append((i, j, nbrs_i))
            if not edges_to_test:
                break

            for i, j, nbrs in edges_to_test:
                if adj[i, j] == 0:
                    continue
                removed = False

                for cond_list in (nbrs, [k for k in range(p) if adj[j, k] == 1 and k != i]):
                    if removed:
                        break
                    if len(cond_list) < depth:
                        continue
                    for S in combinations(cond_list, depth):
                        S = list(S)
                        pc = self._partial_corr(corr, i, j, S)
                        z = 0.5 * np.log((1.0 + pc) / (1.0 - pc + 1e-10))
                        stat = abs(z) * np.sqrt(n_samples - len(S) - 3)
                        p_val = 2.0 * (1.0 - stats.norm.cdf(stat))
                        if p_val > alpha:
                            adj[i, j] = adj[j, i] = 0
                            sep_set[i][j] = sep_set[j][i] = set(S)
                            removed = True
                            break

            depth += 1

        edges = [(i, j) for i in range(p) for j in range(i + 1, p) if adj[i, j]]

        return {
            "skeleton": adj,
            "edges": edges,
            "separation_sets": sep_set,
            "n_edges": len(edges),
            "n_nodes": p,
        }

    @staticmethod
    def _partial_corr(corr, i, j, S):
        """Partial correlation of (i, j) given set S via sub-matrix inversion."""
        if not S:
            return float(corr[i, j])
        idx = [i, j] + list(S)
        sub = corr[np.ix_(idx, idx)]
        try:
            prec = np.linalg.inv(sub)
            pc = -prec[0, 1] / np.sqrt(abs(prec[0, 0] * prec[1, 1]) + 1e-12)
        except np.linalg.LinAlgError:
            pc = 0.0
        return float(np.clip(pc, -1.0, 1.0))

    # ---- DAG topological sort ----------------------------------------------- #

    def dag_topological_order(self, adjacency):
        """Topological sort (Kahn's algorithm) and cycle detection.

        Parameters
        ----------
        adjacency : (N, N) array-like
            Directed adjacency matrix (*A[i,j] > 0* means edge i→j).

        Returns
        -------
        dict with keys: ordering, is_dag, has_cycle, cycle_nodes,
        n_nodes, n_ordered
        """
        A = np.asarray(adjacency, dtype=int)
        n = A.shape[0]

        in_deg = A.sum(axis=0)
        queue = sorted(int(i) for i in range(n) if in_deg[i] == 0)
        order = []

        while queue:
            node = queue.pop(0)
            order.append(node)
            for j in range(n):
                if A[node, j] > 0:
                    in_deg[j] -= 1
                    if in_deg[j] == 0:
                        queue.append(j)
                        queue.sort()  # deterministic tie-breaking

        is_dag = len(order) == n
        cycle_nodes = sorted(set(range(n)) - set(order)) if not is_dag else []

        return {
            "ordering": order,
            "is_dag": is_dag,
            "has_cycle": not is_dag,
            "cycle_nodes": cycle_nodes,
            "n_nodes": n,
            "n_ordered": len(order),
        }
