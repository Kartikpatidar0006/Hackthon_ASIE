"""Tests for the NLP Skill Extractor."""
import pytest
from asie.nlp import skill_extractor


class TestSkillExtractor:
    def test_extract_basic_skills(self):
        text = "Looking for a Python developer with machine learning experience and AWS knowledge."
        skills = skill_extractor.extract(text)
        assert "python" in skills
        assert "machine_learning" in skills
        assert "aws" in skills

    def test_extract_aliases(self):
        text = "Must know ML, NLP, and k8s. React.js experience preferred."
        skills = skill_extractor.extract(text)
        assert "machine_learning" in skills
        assert "natural_language_processing" in skills
        assert "kubernetes" in skills
        assert "react" in skills

    def test_extract_empty_text(self):
        assert skill_extractor.extract("") == []
        assert skill_extractor.extract("   ") == []

    def test_extract_with_confidence(self):
        text = "Expert in deep learning and computer vision with 8 years of experience."
        results = skill_extractor.extract_with_confidence(text)
        assert len(results) > 0
        # Each result is (skill_name, confidence)
        for name, conf in results:
            assert 0 <= conf <= 1.0

    def test_extract_from_resume(self):
        resume = """
        Senior Data Scientist with 5 years experience.
        Expert in Python, machine learning, and deep learning.
        Familiar with Docker and Kubernetes.
        Basic knowledge of blockchain.
        """
        skills = skill_extractor.extract_from_resume(resume)
        assert "python" in skills
        assert "machine_learning" in skills
        # Expert skills should have higher proficiency
        assert skills.get("python", 0) > skills.get("blockchain", 0)

    def test_no_false_positives(self):
        text = "I went to the store and bought some apples."
        skills = skill_extractor.extract(text)
        assert len(skills) == 0
