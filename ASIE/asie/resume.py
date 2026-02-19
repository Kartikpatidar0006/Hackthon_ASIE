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
from asie.models import Industry, ResumeAnalysis, RiskLevel, RoleFitResult, SkillGap
from asie.nlp import skill_extractor
from asie.taxonomy import (
    JOB_ROLE_PROFILES,
    get_role_demand_profile,
    get_roles_for_industry,
    taxonomy_index,
)


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
        target_role: Optional[str] = None,
        market_demand: Optional[Dict[str, float]] = None,
    ) -> ResumeAnalysis:
        """
        Perform a full skill gap analysis.

        Parameters
        ----------
        resume_text : raw resume text
        target_industry : optional industry filter
        target_geo : optional geo filter
        target_role : job role id (e.g. 'ai_engineer', 'full_stack_developer').
                      When set, gaps & readiness are scored against the role's
                      specific demand profile and enriched with 3-5 yr trend data.
        market_demand : dict of {skill_id: demand_score (0-1)}
                        If None, uses role-specific or default demand profile.
        """
        # Step 1: Privacy sanitization
        sanitized = self.privacy.sanitize(resume_text)
        logger.info("Resume sanitized – PII removed")

        # Step 2: Extract skills from resume
        user_skills = skill_extractor.extract_from_resume(sanitized)
        logger.info(f"Extracted {len(user_skills)} skills from resume")

        # Step 3: Build market demand profile
        #   Priority: target_role > target_industry > generic
        role_profile = None
        if target_role:
            role_demand = get_role_demand_profile(target_role)
            role_profile = JOB_ROLE_PROFILES.get(target_role)
            if role_demand:
                logger.info(f"Using role-specific demand for '{target_role}'")
                # Apply future demand multiplier to project 3-5yr relevance
                multiplier = role_profile.future_demand_multiplier if role_profile else 1.0
                market_demand = {
                    sk: min(v * multiplier, 1.0) for sk, v in role_demand.items()
                }
            else:
                logger.warning(f"Unknown role '{target_role}', falling back")

        if market_demand is None:
            market_demand = self._default_demand_profile(target_industry)

        # Step 4: Compute gaps (with future trend hints)
        gaps = self._compute_gaps(user_skills, market_demand, role_profile)

        # Step 5: Compute overall readiness
        readiness = self._compute_readiness(user_skills, market_demand)

        # Step 6: Industry fit scores
        industry_fit = self._compute_industry_fit(user_skills)

        # Step 7: Top recommended skills
        recommended = self._get_recommendations(user_skills, gaps)

        # Step 8: Role fit scores
        role_fits = self._compute_role_fits(user_skills, target_industry)
        target_role_readiness = None
        if target_role:
            # Put the selected role first, then top 4 alternatives
            selected = [rf for rf in role_fits if rf.role_id == target_role]
            others = [rf for rf in role_fits if rf.role_id != target_role][:4]
            role_fits = selected + others
            if selected:
                target_role_readiness = selected[0].readiness_score
        else:
            role_fits = role_fits[:8]  # Limit to top 8 when no role selected

        logger.info(
            f"Analysis complete: {len(user_skills)} skills, {len(gaps)} gaps, "
            f"role={target_role}, demand_keys={len(market_demand)}"
        )

        return ResumeAnalysis(
            extracted_skills=list(user_skills.keys()),
            skill_gaps=gaps,
            overall_readiness_score=readiness,
            top_recommended_skills=recommended,
            industry_fit=industry_fit,
            target_role=target_role,
            role_readiness_score=target_role_readiness,
            role_fit_results=role_fits,
        )

    def _compute_gaps(
        self,
        user_skills: Dict[str, float],
        market_demand: Dict[str, float],
        role_profile: Any = None,
    ) -> List[SkillGap]:
        """Identify and score skill gaps with 3-5yr trend annotations.

        Philosophy:
        - If user lists skill on resume → they HAVE it → gap is minimal.
        - Only skills MISSING from the resume (user_level=0) are real gaps.
        - Skills the user has but at lower proficiency get a small gap.
        """
        gaps: List[SkillGap] = []

        for skill_id, demand in market_demand.items():
            user_level = user_skills.get(skill_id, 0.0)

            if user_level > 0:
                # User has this skill — only flag if well below demand
                gap_score = max(0, demand - user_level)
                if gap_score < 0.25:
                    continue  # Close enough — no meaningful gap
            else:
                # Skill completely missing from resume — real gap
                gap_score = demand  # Full demand is the gap

            if gap_score < 0.15:
                continue  # Skip tiny gaps

            # Priority based on whether skill is missing vs weak
            if user_level == 0 and demand > 0.7:
                priority = RiskLevel.CRITICAL  # Missing + high demand
            elif user_level == 0 and demand > 0.4:
                priority = RiskLevel.HIGH      # Missing + moderate demand
            elif gap_score > 0.4:
                priority = RiskLevel.MEDIUM     # User has it but weak
            else:
                priority = RiskLevel.LOW

            # Build future-trend hint
            future_trend = self._trend_hint(skill_id, demand, role_profile)

            # Get learning path recommendations
            resources = self._suggest_resources(skill_id)

            gaps.append(SkillGap(
                skill_name=skill_id,
                current_level=round(user_level, 3),
                market_demand=round(demand, 3),
                gap_score=round(gap_score, 3),
                priority=priority,
                recommended_resources=resources,
                growth_forecast=round(demand * 1.2, 3),
                future_trend=future_trend,
            ))

        # Sort: missing skills first (user_level=0), then by gap score
        gaps.sort(key=lambda g: (-int(g.current_level == 0), -g.gap_score))
        return gaps[:10]  # Top 10 most critical gaps only

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

    # ── Role-based helpers ─────────────────────────────────────────────────

    @staticmethod
    def _trend_hint(skill_id: str, demand: float, role_profile: Any = None) -> str:
        """Return a human-readable 3-5yr trend string for a skill."""
        multiplier = role_profile.future_demand_multiplier if role_profile else 1.0
        projected = min(demand * multiplier, 1.0)
        delta = projected - demand

        if delta > 0.10:
            return f"\u2191\u2191 Very high demand in 3-5 yrs (projected {projected:.0%})"
        elif delta > 0.03:
            return f"\u2191 Growing demand in 3-5 yrs (projected {projected:.0%})"
        elif delta > -0.03:
            return f"\u2192 Stable demand (projected {projected:.0%})"
        else:
            return f"\u2193 Declining demand (projected {projected:.0%})"

    def _compute_role_fits(
        self,
        user_skills: Dict[str, float],
        target_industry: Optional[str] = None,
    ) -> List[RoleFitResult]:
        """Score how well a user fits relevant job roles."""
        profiles = (
            get_roles_for_industry(target_industry)
            if target_industry
            else list(JOB_ROLE_PROFILES.values())
        )
        results: List[RoleFitResult] = []
        for profile in profiles:
            results.append(self._score_single_role(user_skills, profile))
        results.sort(key=lambda r: r.readiness_score, reverse=True)
        return results

    @staticmethod
    def _score_single_role(
        user_skills: Dict[str, float],
        profile: Any,
    ) -> RoleFitResult:
        """Compute readiness for one job role."""
        matched, missing_req, missing_pref = [], [], []

        total_w, total_cov = 0.0, 0.0
        for sk, imp in profile.required_skills.items():
            level = user_skills.get(sk, 0.0)
            cov = min(level / (imp + 1e-8), 1.0)
            total_w += imp
            total_cov += cov * imp
            (matched if level >= 0.1 else missing_req).append(sk)

        for sk, imp in profile.preferred_skills.items():
            level = user_skills.get(sk, 0.0)
            w = imp * 0.5
            cov = min(level / (imp + 1e-8), 1.0)
            total_w += w
            total_cov += cov * w
            if level >= 0.1:
                if sk not in matched:
                    matched.append(sk)
            else:
                missing_pref.append(sk)

        readiness = round(float(np.clip(total_cov / (total_w + 1e-8), 0, 1)), 4)

        return RoleFitResult(
            role_id=profile.role_id,
            role_name=profile.display_name,
            readiness_score=readiness,
            matched_skills=matched,
            missing_required=missing_req,
            missing_preferred=missing_pref,
            trend_outlook=profile.trend_outlook,
            future_demand_multiplier=profile.future_demand_multiplier,
        )


# Module-level singleton
resume_analyzer = ResumeAnalyzer()
