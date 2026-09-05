"""
BioNEETPro - Typed Biology Concept Graph Engine
Represents and traverses 10 canonical biological relationships:
- IS_A
- PART_OF
- RELATED_TO
- CAUSES
- RESULTS_IN
- REQUIRED_FOR
- PRECEDES
- CONTRASTS_WITH
- EXAMPLE_OF
- PREREQUISITE_OF
"""

from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

GRAPH_CSV = Path(__file__).resolve().parent / "data" / "concept_dependency_graph.csv"


class BiologyConceptGraph:
    """
    Multi-relational directed graph of NCERT Biology concepts.
    Enables causal reasoning, prerequisite tracing, and conceptual contrast identification.
    """

    RELATIONSHIPS = {
        "IS_A",
        "PART_OF",
        "RELATED_TO",
        "CAUSES",
        "RESULTS_IN",
        "REQUIRED_FOR",
        "PRECEDES",
        "CONTRASTS_WITH",
        "EXAMPLE_OF",
        "PREREQUISITE_OF",
    }

    def __init__(self, graph_path: Path = GRAPH_CSV):
        self.graph_path = graph_path
        self.adj_out: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.adj_in: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.nodes: Dict[str, str] = {}
        self.load_graph()

    def find_concept_by_title(self, title: str) -> Optional[str]:
        """Finds a concept ID by doing a case-insensitive title lookup."""
        title_lower = title.lower()
        for cid, ctitle in self.nodes.items():
            if ctitle.lower() == title_lower:
                return cid
        return None

    def get_all_related(self, concept_id: str, max_hops: int = 2) -> List[Dict]:
        """Returns a flat list of all related concepts with distances and relationship types."""
        if concept_id not in self.nodes and concept_id not in self.adj_out and concept_id not in self.adj_in:
            return []

        results = []
        visited = {concept_id}
        queue = deque([(concept_id, 0, None)])

        while queue:
            curr, dist, rel = queue.popleft()
            if dist > 0:
                results.append({
                    "concept_id": curr,
                    "title": self.nodes.get(curr, curr),
                    "distance": dist,
                    "relationship": rel
                })
            
            if dist < max_hops:
                for edge in self.adj_out.get(curr, []):
                    nxt = edge["target_id"]
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append((nxt, dist + 1, edge["relationship"]))
                for edge in self.adj_in.get(curr, []):
                    nxt = edge["source_id"]
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append((nxt, dist + 1, edge["relationship"]))

        return results

    def load_graph(self):
        self.adj_out.clear()
        self.adj_in.clear()
        self.nodes.clear()

        if not self.graph_path.exists():
            return

        df = pd.read_csv(self.graph_path)
        for _, row in df.iterrows():
            if pd.isna(row.get("source_concept_id")) or pd.isna(row.get("target_concept_id")):
                continue
            src_id = str(row["source_concept_id"]).strip()
            src_title = str(row["source_title"]).strip()
            tgt_id = str(row["target_concept_id"]).strip()
            tgt_title = str(row["target_title"]).strip()
            rel = str(row["relationship"]).strip().upper()
            chap = str(row.get("chapter_id", "")).strip()
            desc = str(row.get("description", "")).strip()

            self.nodes[src_id] = src_title
            self.nodes[tgt_id] = tgt_title

            edge = {
                "source_id": src_id,
                "source_title": src_title,
                "target_id": tgt_id,
                "target_title": tgt_title,
                "relationship": rel,
                "chapter_id": chap,
                "description": desc,
            }

            self.adj_out[src_id].append(edge)
            self.adj_in[tgt_id].append(edge)

    def get_neighbors(self, concept_id: str, rel_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns outbound connected concepts, optionally filtered by relationship type."""
        edges = self.adj_out.get(concept_id, [])
        if rel_type:
            rel_upper = rel_type.upper()
            return [e for e in edges if e["relationship"] == rel_upper]
        return edges

    def get_prerequisites(self, concept_id: str) -> List[Dict[str, Any]]:
        """
        Finds foundational prerequisites needed before learning this concept:
        - Outbound PREREQUISITE_OF edges (where this concept requires another)
        - Inbound REQUIRED_FOR edges (where another concept is required for this)
        """
        prereqs = []
        # Check inbound REQUIRED_FOR
        for e in self.adj_in.get(concept_id, []):
            if e["relationship"] in {"REQUIRED_FOR", "PREREQUISITE_OF"}:
                prereqs.append({
                    "concept_id": e["source_id"],
                    "title": e["source_title"],
                    "relationship": e["relationship"],
                    "description": e["description"]
                })
        # Check outbound PREREQUISITE_OF
        for e in self.adj_out.get(concept_id, []):
            if e["relationship"] in {"REQUIRED_FOR", "PREREQUISITE_OF"}:
                prereqs.append({
                    "concept_id": e["target_id"],
                    "title": e["target_title"],
                    "relationship": e["relationship"],
                    "description": e["description"]
                })
        return prereqs

    def get_causal_chain(self, concept_id: str, max_depth: int = 3) -> List[Dict[str, Any]]:
        """
        Traces downstream cause-and-effect chains (CAUSES, RESULTS_IN).
        Example: Insulin -> Glucose uptake -> Blood glucose reduction
        """
        chain = []
        visited: Set[str] = {concept_id}
        curr_id = concept_id

        for _ in range(max_depth):
            causal_edges = [
                e for e in self.adj_out.get(curr_id, [])
                if e["relationship"] in {"CAUSES", "RESULTS_IN"} and e["target_id"] not in visited
            ]
            if not causal_edges:
                break
            step_edge = causal_edges[0]
            chain.append({
                "from_concept": step_edge["source_title"],
                "relationship": step_edge["relationship"],
                "to_concept": step_edge["target_title"],
                "target_id": step_edge["target_id"],
                "description": step_edge["description"]
            })
            visited.add(step_edge["target_id"])
            curr_id = step_edge["target_id"]

        return chain

    def get_contrasting_concepts(self, concept_id: str) -> List[Dict[str, Any]]:
        """
        Finds paired concepts commonly contrasted in NEET (e.g. C3 vs C4, Mitosis vs Meiosis).
        """
        contrasts = []
        for e in self.adj_out.get(concept_id, []):
            if e["relationship"] == "CONTRASTS_WITH":
                contrasts.append({
                    "concept_id": e["target_id"],
                    "title": e["target_title"],
                    "description": e["description"]
                })
        for e in self.adj_in.get(concept_id, []):
            if e["relationship"] == "CONTRASTS_WITH":
                contrasts.append({
                    "concept_id": e["source_id"],
                    "title": e["source_title"],
                    "description": e["description"]
                })
        return contrasts

    def traverse_related_concepts(self, concept_id: str, max_hops: int = 2) -> List[Dict[str, Any]]:
        """
        Breadth-first search traversal returning nearby knowledge nodes and semantic proximity.
        """
        if concept_id not in self.nodes and concept_id not in self.adj_out:
            return []

        results = []
        visited: Set[str] = {concept_id}
        queue = deque([(concept_id, 0)])

        while queue:
            curr, dist = queue.popleft()
            if dist > 0:
                results.append({
                    "concept_id": curr,
                    "title": self.nodes.get(curr, curr),
                    "graph_distance": dist
                })
            if dist < max_hops:
                for edge in self.adj_out.get(curr, []):
                    nxt = edge["target_id"]
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append((nxt, dist + 1))
                for edge in self.adj_in.get(curr, []):
                    nxt = edge["source_id"]
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append((nxt, dist + 1))

        return results


concept_graph = BiologyConceptGraph()
