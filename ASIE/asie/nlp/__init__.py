"""
NLP-based Skill Extraction Engine.

Extracts skill mentions from unstructured text (job descriptions, patent
abstracts, research paper titles/abstracts, resumes) and maps them to the
canonical taxonomy.

Uses a combination of:
    - Rule-based pattern matching against taxonomy aliases
    - N-gram extraction with fuzzy matching
    - Optional spaCy NER pipeline for entity recognition
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Dict, List, Optional, Set, Tuple

from loguru import logger

from asie.taxonomy import SKILL_TAXONOMY, TaxonomySkill, taxonomy_index


class SkillExtractor:
    """Extract and map skills from unstructured text."""

    def __init__(self, fuzzy_threshold: float = 0.75) -> None:
        self.fuzzy_threshold = fuzzy_threshold
        # Pre-compile regex patterns for fast matching
        self._patterns: List[Tuple[re.Pattern, str]] = []
        self._build_patterns()

    def _build_patterns(self) -> None:
        """Build compiled regex patterns from all taxonomy aliases."""
        for sk in SKILL_TAXONOMY:
            # Add canonical name (with underscores replaced by spaces/hyphens)
            variants = set()
            variants.add(sk.canonical.replace("_", " "))
            variants.add(sk.canonical.replace("_", "-"))
            variants.add(sk.canonical)
            for alias in sk.aliases:
                variants.add(alias)
            for variant in variants:
                try:
                    # Word-boundary matching, case-insensitive
                    escaped = re.escape(variant)
                    pattern = re.compile(r'\b' + escaped + r'\b', re.IGNORECASE)
                    self._patterns.append((pattern, sk.canonical))
                except re.error:
                    logger.warning(f"Failed to compile regex for: {variant}")

    def extract(self, text: str) -> List[str]:
        """
        Extract canonical skill names from text.

        Returns deduplicated list of canonical skill identifiers ordered by
        their first appearance in the text.
        """
        if not text or not text.strip():
            return []

        found: Dict[str, int] = {}  # canonical -> first position
        text_lower = text.lower()

        # Phase 1: Exact pattern matching
        for pattern, canonical in self._patterns:
            match = pattern.search(text)
            if match and canonical not in found:
                found[canonical] = match.start()

        # Phase 2: N-gram fuzzy matching for remaining skills
        words = re.findall(r'\b\w+(?:\s+\w+){0,2}\b', text_lower)
        for ngram in words:
            ngram_clean = ngram.strip()
            if len(ngram_clean) < 2:
                continue
            match = taxonomy_index.fuzzy_match(ngram_clean, self.fuzzy_threshold)
            if match and match not in found:
                pos = text_lower.find(ngram_clean)
                found[match] = pos if pos >= 0 else len(text)

        # Order by first appearance
        sorted_skills = sorted(found.items(), key=lambda x: x[1])
        return [s[0] for s in sorted_skills]

    def extract_with_confidence(self, text: str) -> List[Tuple[str, float]]:
        """
        Extract skills with a confidence score.

        Returns list of (canonical_name, confidence) tuples.
        Confidence is based on match quality and frequency.
        """
        if not text or not text.strip():
            return []

        scores: Dict[str, float] = {}
        text_lower = text.lower()

        # Exact matches get high confidence
        for pattern, canonical in self._patterns:
            matches = pattern.findall(text)
            if matches:
                # More mentions → higher confidence, capped at 1.0
                freq_boost = min(len(matches) * 0.1, 0.3)
                scores[canonical] = min(0.9 + freq_boost, 1.0)

        # Fuzzy matches get proportional confidence
        words = re.findall(r'\b\w+(?:\s+\w+){0,2}\b', text_lower)
        token_counter = Counter(words)
        for ngram, count in token_counter.items():
            ngram_clean = ngram.strip()
            if len(ngram_clean) < 2:
                continue
            match = taxonomy_index.fuzzy_match(ngram_clean, self.fuzzy_threshold)
            if match and match not in scores:
                # Fuzzy confidence is lower
                from difflib import SequenceMatcher
                best_alias_score = 0.0
                sk_info = taxonomy_index.get(match)
                if sk_info:
                    for alias in [sk_info.canonical.replace("_", " ")] + sk_info.aliases:
                        s = SequenceMatcher(None, ngram_clean, alias.lower()).ratio()
                        best_alias_score = max(best_alias_score, s)
                freq_boost = min(count * 0.05, 0.15)
                scores[match] = min(best_alias_score + freq_boost, 0.95)

        return sorted(scores.items(), key=lambda x: -x[1])

    def extract_from_resume(self, resume_text: str) -> Dict[str, float]:
        """
        Specialised extraction for resumes.

        Returns dict of {canonical_skill: estimated_proficiency_level (0-1)}.
        Proficiency is heuristically estimated from:
            - Frequency of mention
            - Context keywords (expert, beginner, familiar, etc.)
            - Section placement (skills section vs general mention)
        """
        skills_conf = self.extract_with_confidence(resume_text)
        result: Dict[str, float] = {}

        # Proficiency context words
        expert_words = {"expert", "advanced", "senior", "lead", "architect", "principal", "mastery", "proficient"}
        intermediate_words = {"intermediate", "experienced", "familiar", "working knowledge", "comfortable"}
        beginner_words = {"beginner", "basic", "learning", "exposure", "introductory", "fundamentals"}

        text_lower = resume_text.lower()

        for skill_name, confidence in skills_conf:
            # Base level from confidence
            base_level = confidence * 0.6

            # Contextual proficiency boost
            # Look for proficiency keywords near the skill mention
            skill_display = skill_name.replace("_", " ")
            skill_pattern = re.compile(
                r'(.{0,50})' + re.escape(skill_display) + r'(.{0,50})',
                re.IGNORECASE
            )
            matches = skill_pattern.findall(text_lower)
            context = " ".join([m[0] + m[1] for m in matches])

            if any(w in context for w in expert_words):
                base_level = min(base_level + 0.35, 1.0)
            elif any(w in context for w in intermediate_words):
                base_level = min(base_level + 0.2, 0.85)
            elif any(w in context for w in beginner_words):
                base_level = min(base_level + 0.05, 0.5)
            else:
                base_level = min(base_level + 0.15, 0.75)

            result[skill_name] = round(base_level, 3)

        return result


# Module-level singleton
skill_extractor = SkillExtractor()
