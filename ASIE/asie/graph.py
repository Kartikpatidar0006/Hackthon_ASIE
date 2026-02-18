"""
Knowledge Graph for Skill Relationships.

Builds and queries a directed graph where:
    - Nodes are skills, domains, technologies, and roles
    - Edges encode: prerequisite, complementary, specialization, parent-child

Backed by NetworkX for the prototype; designed to be replaceable with
Neo4j / Amazon Neptune in production.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx
from loguru import logger

from asie.models import GraphEdge, GraphNode
from asie.taxonomy import (
    DOMAIN_INDUSTRY_MAP,
    SKILL_RELATIONSHIPS,
    SKILL_TAXONOMY,
    TaxonomySkill,
    taxonomy_index,
)


class SkillKnowledgeGraph:
    """In-memory knowledge graph of skill relationships."""

    def __init__(self) -> None:
        self.graph = nx.DiGraph()
        self._built = False

    # ── Construction ─────────────────────────────────────────────────────

    def build(self) -> None:
        """Build the full graph from the taxonomy and relationship ontology."""
        if self._built:
            return

        # Add skill nodes
        for sk in SKILL_TAXONOMY:
            self.graph.add_node(
                sk.canonical,
                label=sk.canonical.replace("_", " ").title(),
                node_type="skill",
                category=sk.category,
                domain=sk.domain,
                automation_risk=sk.automation_risk_base,
            )

        # Add domain nodes
        for domain in set(sk.domain for sk in SKILL_TAXONOMY):
            self.graph.add_node(
                f"domain:{domain}",
                label=domain.replace("_", " ").title(),
                node_type="domain",
                category="domain",
                domain=domain,
            )

        # Add industry nodes
        for industry, domains in DOMAIN_INDUSTRY_MAP.items():
            for ind in DOMAIN_INDUSTRY_MAP.get(industry, []):
                ind_key = f"industry:{ind}"
                if not self.graph.has_node(ind_key):
                    self.graph.add_node(
                        ind_key,
                        label=ind.replace("_", " ").title(),
                        node_type="industry",
                        category="industry",
                        domain=ind,
                    )

        # Skill → Domain edges
        for sk in SKILL_TAXONOMY:
            self.graph.add_edge(
                sk.canonical,
                f"domain:{sk.domain}",
                relationship="belongs_to",
                weight=1.0,
            )

        # Domain → Industry edges
        for domain, industries in DOMAIN_INDUSTRY_MAP.items():
            for ind in industries:
                dom_key = f"domain:{domain}"
                ind_key = f"industry:{ind}"
                if self.graph.has_node(dom_key) and self.graph.has_node(ind_key):
                    self.graph.add_edge(
                        dom_key, ind_key, relationship="relevant_to", weight=0.8
                    )

        # Parent-child edges from taxonomy
        for sk in SKILL_TAXONOMY:
            if sk.parent:
                self.graph.add_edge(
                    sk.canonical, sk.parent, relationship="child_of", weight=0.9
                )

        # Skill-skill relationship edges
        for src, tgt, rel_type, weight in SKILL_RELATIONSHIPS:
            if self.graph.has_node(src) and self.graph.has_node(tgt):
                self.graph.add_edge(
                    src, tgt, relationship=rel_type, weight=weight
                )

        self._built = True
        logger.info(
            f"Knowledge graph built: {self.graph.number_of_nodes()} nodes, "
            f"{self.graph.number_of_edges()} edges"
        )

    # ── Queries ──────────────────────────────────────────────────────────

    def get_neighbors(
        self, skill: str, depth: int = 1, relationship: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get neighboring nodes up to *depth* hops."""
        self.build()
        if skill not in self.graph:
            return []
        neighbors: List[Dict[str, Any]] = []
        visited: Set[str] = {skill}
        frontier = [(skill, 0)]
        while frontier:
            current, d = frontier.pop(0)
            if d >= depth:
                continue
            for _, nbr, data in self.graph.edges(current, data=True):
                if relationship and data.get("relationship") != relationship:
                    continue
                if nbr not in visited:
                    visited.add(nbr)
                    node_data = dict(self.graph.nodes[nbr])
                    neighbors.append({
                        "id": nbr,
                        "distance": d + 1,
                        "relationship": data.get("relationship", ""),
                        "weight": data.get("weight", 1.0),
                        **node_data,
                    })
                    frontier.append((nbr, d + 1))
            # Also check reverse edges
            for pred, _, data in self.graph.in_edges(current, data=True):
                if relationship and data.get("relationship") != relationship:
                    continue
                if pred not in visited:
                    visited.add(pred)
                    node_data = dict(self.graph.nodes[pred])
                    neighbors.append({
                        "id": pred,
                        "distance": d + 1,
                        "relationship": data.get("relationship", "") + " (reverse)",
                        "weight": data.get("weight", 1.0),
                        **node_data,
                    })
                    frontier.append((pred, d + 1))
        return neighbors

    def get_prerequisites(self, skill: str) -> List[str]:
        """Return prerequisite skills (direct and transitive)."""
        self.build()
        prereqs: List[str] = []
        for _, tgt, data in self.graph.edges(skill, data=True):
            if data.get("relationship") == "prerequisite":
                prereqs.append(tgt)
                prereqs.extend(self.get_prerequisites(tgt))
        return list(dict.fromkeys(prereqs))  # dedupe preserving order

    def get_complementary(self, skill: str) -> List[str]:
        """Return complementary skills."""
        self.build()
        comps: List[str] = []
        for _, tgt, data in self.graph.edges(skill, data=True):
            if data.get("relationship") == "complementary":
                comps.append(tgt)
        for pred, _, data in self.graph.in_edges(skill, data=True):
            if data.get("relationship") == "complementary":
                comps.append(pred)
        return list(set(comps))

    def get_skills_for_industry(self, industry: str) -> List[str]:
        """Return all skills relevant to an industry."""
        self.build()
        ind_key = f"industry:{industry}"
        if ind_key not in self.graph:
            return []
        skills: List[str] = []
        # Industry ← Domain ← Skill
        for pred, _, _ in self.graph.in_edges(ind_key, data=True):
            if pred.startswith("domain:"):
                for sk_pred, _, _ in self.graph.in_edges(pred, data=True):
                    if not sk_pred.startswith("domain:") and not sk_pred.startswith("industry:"):
                        skills.append(sk_pred)
        return list(set(skills))

    def get_skill_centrality(self) -> Dict[str, float]:
        """Compute PageRank centrality for skill nodes."""
        self.build()
        pr = nx.pagerank(self.graph, weight="weight")
        return {
            k: v for k, v in sorted(pr.items(), key=lambda x: -x[1])
            if not k.startswith("domain:") and not k.startswith("industry:")
        }

    def get_learning_path(self, from_skill: str, to_skill: str) -> List[str]:
        """Find shortest skill-acquisition path between two skills."""
        self.build()
        try:
            path = nx.shortest_path(self.graph, from_skill, to_skill)
            # Filter to skill nodes only
            return [n for n in path if not n.startswith("domain:") and not n.startswith("industry:")]
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def to_serializable(self) -> Dict[str, Any]:
        """Export graph as JSON-serializable dict for the API."""
        self.build()
        nodes = []
        for n, data in self.graph.nodes(data=True):
            nodes.append({"id": n, **data})
        edges = []
        for u, v, data in self.graph.edges(data=True):
            edges.append({"source": u, "target": v, **data})
        return {"nodes": nodes, "edges": edges}


# Module-level singleton
skill_graph = SkillKnowledgeGraph()
