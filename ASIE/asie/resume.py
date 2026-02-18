"""
Privacy-Preserving Resume Skill Gap Analysis.

Processes a resume to:
    1. Extract skills using NLP (no PII stored)
    2. Compare against current market demand
    3. Identify gaps and rank by priority
    4. Recommend learning paths using the knowledge graph
    5. Score overall future-readiness

Privacy measures:
    - Text is processed in-memory only (never persisted)
    - PII is stripped before processing
    - Only anonymised skill vectors are stored
    - All outputs are keyed by anonymous analysis IDs
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Optional

import numpy as np
from loguru import logger

from asie.config import settings
from asie.graph import skill_graph
from asie.models import Industry, ResumeAnalysis, RiskLevel, SkillGap
from asie.nlp import skill_extractor
from asie.taxonomy import taxonomy_index


class PrivacyGuard:
    """Strip and hash PII from resume text before processing."""

    # Patterns for PII detection
    EMAIL_RE = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_RE = re.compile(r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]{7,15}')
    SSN_RE = re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b')
    URL_RE = re.compile(r'https?://\S+|www\.\S+')
    NAME_INDICATORS = re.compile(
        r'^[A-Z][a-z]+\s+[A-Z][a-z]+',
        re.MULTILINE
    )

    @classmethod
    def sanitize(cls, text: str) -> str:
        """Remove PII from text, keeping skill-relevant content."""
        sanitized = text
        sanitized = cls.EMAIL_RE.sub("[EMAIL]", sanitized)
        sanitized = cls.PHONE_RE.sub("[PHONE]", sanitized)
        sanitized = cls.SSN_RE.sub("[SSN]", sanitized)
        sanitized = cls.URL_RE.sub("[URL]", sanitized)
        # Remove first line if it looks like a name
        lines = sanitized.split('\n')
        if lines and cls.NAME_INDICATORS.match(lines[0]):
            lines[0] = "[NAME]"
        sanitized = '\n'.join(lines)
        return sanitized

    @staticmethod
    def hash_text(text: str) -> str:
        """Create a one-way hash of the full text for deduplication."""
        salted = settings.hash_salt + text
        return hashlib.sha256(salted.encode()).hexdigest()[:16]


class ResumeAnalyzer:
    """Analyse a resume for skill gaps against market demand."""

    def __init__(self) -> None:
        self.privacy = PrivacyGuard()

    def analyze(
        self,
        resume_text: str,
        target_industry: Optional[str] = None,
        target_geo: Optional[str] = None,
        market_demand: Optional[Dict[str, float]] = None,
    ) -> ResumeAnalysis:
        """
        Perform a full skill gap analysis.

        Parameters
        ----------
        resume_text : raw resume text
        target_industry : optional industry filter
        target_geo : optional geo filter
        market_demand : dict of {skill_id: demand_score (0-1)}
                        If None, uses a default demand profile.
        """
        # Step 1: Privacy sanitization
        sanitized = self.privacy.sanitize(resume_text)
        logger.info("Resume sanitized – PII removed")

        # Step 2: Extract skills from resume
        user_skills = skill_extractor.extract_from_resume(sanitized)
        logger.info(f"Extracted {len(user_skills)} skills from resume")

        # Step 3: Build market demand profile
        if market_demand is None:
            market_demand = self._default_demand_profile(target_industry)

        # Step 4: Compute gaps
        gaps = self._compute_gaps(user_skills, market_demand)

        # Step 5: Compute overall readiness
        readiness = self._compute_readiness(user_skills, market_demand)

        # Step 6: Industry fit scores
        industry_fit = self._compute_industry_fit(user_skills)

        # Step 7: Top recommended skills
        recommended = self._get_recommendations(user_skills, gaps)

        return ResumeAnalysis(
            extracted_skills=list(user_skills.keys()),
            skill_gaps=gaps,
            overall_readiness_score=readiness,
            top_recommended_skills=recommended,
            industry_fit=industry_fit,
        )

    def _compute_gaps(
        self,
        user_skills: Dict[str, float],
        market_demand: Dict[str, float],
    ) -> List[SkillGap]:
        """Identify and score skill gaps."""
        gaps: List[SkillGap] = []

        for skill_id, demand in market_demand.items():
            user_level = user_skills.get(skill_id, 0.0)
            gap_score = max(0, demand - user_level)

            if gap_score < 0.1:
                continue  # No meaningful gap

            # Priority based on gap magnitude and demand
            if gap_score > 0.6 and demand > 0.7:
                priority = RiskLevel.CRITICAL
            elif gap_score > 0.4:
                priority = RiskLevel.HIGH
            elif gap_score > 0.2:
                priority = RiskLevel.MEDIUM
            else:
                priority = RiskLevel.LOW

            # Get learning path recommendations
            resources = self._suggest_resources(skill_id)

            gaps.append(SkillGap(
                skill_name=skill_id,
                current_level=round(user_level, 3),
                market_demand=round(demand, 3),
                gap_score=round(gap_score, 3),
                priority=priority,
                recommended_resources=resources,
                growth_forecast=round(demand * 1.2, 3),  # simplified
            ))

        # Sort by gap score desc
        gaps.sort(key=lambda g: g.gap_score, reverse=True)
        return gaps[:20]  # Top 20 gaps

    def _compute_readiness(
        self,
        user_skills: Dict[str, float],
        market_demand: Dict[str, float],
    ) -> float:
        """Compute overall future-readiness score (0-1)."""
        if not market_demand:
            return 0.5

        total_coverage = 0.0
        total_weight = 0.0
        for skill_id, demand in market_demand.items():
            user_level = user_skills.get(skill_id, 0.0)
            coverage = min(user_level / (demand + 1e-8), 1.0)
            total_coverage += coverage * demand
            total_weight += demand

        if total_weight == 0:
            return 0.5
        return round(float(np.clip(total_coverage / total_weight, 0, 1)), 4)

    def _compute_industry_fit(
        self, user_skills: Dict[str, float]
    ) -> Dict[str, float]:
        """Score how well user skills fit each industry."""
        fit_scores: Dict[str, float] = {}
        for industry in Industry:
            industry_skills = skill_graph.get_skills_for_industry(industry.value)
            if not industry_skills:
                fit_scores[industry.value] = 0.0
                continue
            matched = sum(
                user_skills.get(sk, 0) for sk in industry_skills
            )
            fit_scores[industry.value] = round(
                matched / len(industry_skills), 4
            )
        return fit_scores

    def _get_recommendations(
        self,
        user_skills: Dict[str, float],
        gaps: List[SkillGap],
    ) -> List[str]:
        """Get top recommended skills to learn."""
        # Filter gaps to critical/high priority
        top_gaps = [g for g in gaps if g.priority in (RiskLevel.CRITICAL, RiskLevel.HIGH)]
        if not top_gaps:
            top_gaps = gaps[:5]

        recommendations = []
        for gap in top_gaps[:10]:
            recommendations.append(gap.skill_name)
            # Also suggest prerequisites
            prereqs = skill_graph.get_prerequisites(gap.skill_name)
            for p in prereqs:
                if p not in user_skills and p not in recommendations:
                    recommendations.append(p)
        return recommendations[:10]

    @staticmethod
    def _suggest_resources(skill_id: str) -> List[str]:
        """Suggest learning resources for a skill."""
        display_name = skill_id.replace("_", " ").title()
        return [
            f"Online course: '{display_name} Fundamentals'",
            f"Hands-on project: Build a {display_name} portfolio project",
            f"Community: Join {display_name} forums and meetups",
        ]

    @staticmethod
    def _default_demand_profile(
        industry: Optional[str] = None,
    ) -> Dict[str, float]:
        """Generate a default market demand profile."""
        # High-demand skills across industries
        demand: Dict[str, float] = {
            "machine_learning": 0.85,
            "python": 0.90,
            "cloud_computing": 0.80,
            "data_science": 0.82,
            "cybersecurity": 0.78,
            "devops": 0.75,
            "generative_ai": 0.88,
            "kubernetes": 0.70,
            "data_engineering": 0.76,
            "typescript": 0.72,
            "react": 0.70,
            "sql": 0.75,
            "mlops": 0.68,
            "deep_learning": 0.74,
            "natural_language_processing": 0.72,
            "leadership": 0.65,
            "communication": 0.70,
            "problem_solving": 0.75,
            "project_management": 0.60,
            "aws": 0.72,
            "docker": 0.68,
            "golang": 0.58,
            "rust": 0.55,
            "blockchain": 0.45,
            "quantum_computing": 0.35,
        }

        # Adjust if industry-specific
        if industry:
            industry_skills = skill_graph.get_skills_for_industry(industry)
            for sk in industry_skills:
                if sk in demand:
                    demand[sk] = min(demand[sk] * 1.2, 1.0)

        return demand


# Module-level singleton
resume_analyzer = ResumeAnalyzer()
