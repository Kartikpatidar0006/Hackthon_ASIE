"""Tests for Taxonomy and Knowledge Graph."""
import pytest
from asie.taxonomy import taxonomy_index, SKILL_TAXONOMY
from asie.graph import SkillKnowledgeGraph


class TestTaxonomy:
    def test_resolve_canonical(self):
        assert taxonomy_index.resolve("python") == "python"
        assert taxonomy_index.resolve("machine_learning") == "machine_learning"

    def test_resolve_alias(self):
        assert taxonomy_index.resolve("ML") == "machine_learning"
        assert taxonomy_index.resolve("k8s") == "kubernetes"
        assert taxonomy_index.resolve("NLP") == "natural_language_processing"

    def test_resolve_unknown(self):
        assert taxonomy_index.resolve("completely_unknown_skill_xyz") is None

    def test_fuzzy_match(self):
        match = taxonomy_index.fuzzy_match("machin learning")
        assert match == "machine_learning"

    def test_all_skills_nonempty(self):
        assert len(taxonomy_index.all_skills()) > 30

    def test_skills_by_domain(self):
        ai_skills = taxonomy_index.skills_by_domain("ai_ml")
        assert len(ai_skills) > 3


class TestKnowledgeGraph:
    def setup_method(self):
        self.graph = SkillKnowledgeGraph()
        self.graph.build()

    def test_graph_built(self):
        assert self.graph.graph.number_of_nodes() > 0
        assert self.graph.graph.number_of_edges() > 0

    def test_get_neighbors(self):
        neighbors = self.graph.get_neighbors("machine_learning", depth=1)
        assert len(neighbors) > 0

    def test_get_prerequisites(self):
        prereqs = self.graph.get_prerequisites("prompt_engineering")
        assert "generative_ai" in prereqs

    def test_get_complementary(self):
        comps = self.graph.get_complementary("mlops")
        assert len(comps) > 0

    def test_get_skills_for_industry(self):
        tech_skills = self.graph.get_skills_for_industry("technology")
        assert len(tech_skills) > 5

    def test_centrality(self):
        centrality = self.graph.get_skill_centrality()
        assert len(centrality) > 0
        # All values should be positive
        assert all(v > 0 for v in centrality.values())

    def test_to_serializable(self):
        data = self.graph.to_serializable()
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) > 0
