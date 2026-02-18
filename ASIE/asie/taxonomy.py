"""
Canonical Skill Taxonomy & Ontology for ASIE.

Provides:
    - A curated canonical skill list with aliases
    - Domain → skill mappings
    - Skill relationship ontology (prerequisite, complementary, parent/child)
    - Helper functions for fuzzy matching to the canonical list
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from difflib import SequenceMatcher


# ── Canonical Skill Registry ──────────────────────────────────────────────

@dataclass
class TaxonomySkill:
    canonical: str
    category: str  # technical | soft | domain | tool | methodology | certification
    aliases: List[str] = field(default_factory=list)
    parent: Optional[str] = None
    domain: str = "general"
    automation_risk_base: float = 0.3  # base automation susceptibility


# fmt: off
SKILL_TAXONOMY: List[TaxonomySkill] = [
    # ── AI / ML ───────────────────────────────────────
    TaxonomySkill("machine_learning",       "technical", ["ml", "machine-learning", "ML"], domain="ai_ml", automation_risk_base=0.15),
    TaxonomySkill("deep_learning",          "technical", ["dl", "deep-learning", "DL"], parent="machine_learning", domain="ai_ml", automation_risk_base=0.12),
    TaxonomySkill("natural_language_processing", "technical", ["nlp", "NLP", "text mining", "text analytics"], parent="machine_learning", domain="ai_ml", automation_risk_base=0.10),
    TaxonomySkill("computer_vision",        "technical", ["cv", "image recognition", "object detection"], parent="deep_learning", domain="ai_ml", automation_risk_base=0.12),
    TaxonomySkill("reinforcement_learning", "technical", ["rl", "RL"], parent="machine_learning", domain="ai_ml", automation_risk_base=0.10),
    TaxonomySkill("generative_ai",          "technical", ["gen ai", "genai", "generative models", "LLM", "large language models"], parent="deep_learning", domain="ai_ml", automation_risk_base=0.08),
    TaxonomySkill("mlops",                  "technical", ["ml ops", "ML engineering", "model deployment"], domain="ai_ml", automation_risk_base=0.20),
    TaxonomySkill("prompt_engineering",      "technical", ["prompt design", "prompt tuning"], parent="generative_ai", domain="ai_ml", automation_risk_base=0.25),

    # ── Data ──────────────────────────────────────────
    TaxonomySkill("data_science",           "technical", ["data analytics", "data analysis"], domain="data", automation_risk_base=0.20),
    TaxonomySkill("data_engineering",       "technical", ["data pipelines", "ETL"], domain="data", automation_risk_base=0.25),
    TaxonomySkill("sql",                    "tool",      ["SQL", "structured query language", "mysql", "postgresql"], domain="data", automation_risk_base=0.35),
    TaxonomySkill("big_data",              "technical", ["hadoop", "spark", "distributed computing"], domain="data", automation_risk_base=0.30),
    TaxonomySkill("data_visualization",     "technical", ["data viz", "dashboarding", "tableau", "power bi"], domain="data", automation_risk_base=0.35),

    # ── Cloud & DevOps ────────────────────────────────
    TaxonomySkill("cloud_computing",        "technical", ["cloud", "cloud services"], domain="cloud", automation_risk_base=0.25),
    TaxonomySkill("aws",                    "tool",      ["amazon web services", "AWS"], parent="cloud_computing", domain="cloud", automation_risk_base=0.28),
    TaxonomySkill("azure",                  "tool",      ["microsoft azure", "Azure"], parent="cloud_computing", domain="cloud", automation_risk_base=0.28),
    TaxonomySkill("gcp",                    "tool",      ["google cloud", "google cloud platform", "GCP"], parent="cloud_computing", domain="cloud", automation_risk_base=0.28),
    TaxonomySkill("kubernetes",             "tool",      ["k8s", "container orchestration"], domain="cloud", automation_risk_base=0.22),
    TaxonomySkill("docker",                 "tool",      ["containers", "containerization"], domain="cloud", automation_risk_base=0.30),
    TaxonomySkill("devops",                 "methodology", ["CI/CD", "continuous integration", "continuous deployment"], domain="cloud", automation_risk_base=0.30),
    TaxonomySkill("infrastructure_as_code", "technical", ["IaC", "terraform", "pulumi", "cloudformation"], domain="cloud", automation_risk_base=0.32),

    # ── Programming ───────────────────────────────────
    TaxonomySkill("python",                 "tool",      ["Python3", "py"], domain="programming", automation_risk_base=0.20),
    TaxonomySkill("javascript",             "tool",      ["JS", "js", "ecmascript"], domain="programming", automation_risk_base=0.25),
    TaxonomySkill("typescript",             "tool",      ["TS", "ts"], parent="javascript", domain="programming", automation_risk_base=0.23),
    TaxonomySkill("rust",                   "tool",      ["Rust lang"], domain="programming", automation_risk_base=0.18),
    TaxonomySkill("golang",                 "tool",      ["go", "Go lang"], domain="programming", automation_risk_base=0.20),
    TaxonomySkill("java",                   "tool",      ["Java", "JVM"], domain="programming", automation_risk_base=0.30),
    TaxonomySkill("cpp",                    "tool",      ["c++", "C++", "cplusplus"], domain="programming", automation_risk_base=0.28),

    # ── Cybersecurity ─────────────────────────────────
    TaxonomySkill("cybersecurity",          "technical", ["infosec", "information security", "cyber security"], domain="security", automation_risk_base=0.15),
    TaxonomySkill("penetration_testing",    "technical", ["pentesting", "pen testing", "ethical hacking"], parent="cybersecurity", domain="security", automation_risk_base=0.18),
    TaxonomySkill("zero_trust",             "methodology", ["zero trust architecture", "ZTA"], parent="cybersecurity", domain="security", automation_risk_base=0.15),
    TaxonomySkill("devsecops",              "methodology", ["DevSecOps", "security automation"], domain="security", automation_risk_base=0.22),

    # ── Web / Mobile ──────────────────────────────────
    TaxonomySkill("react",                  "tool",      ["reactjs", "react.js", "React"], domain="web", automation_risk_base=0.30),
    TaxonomySkill("nextjs",                 "tool",      ["next.js", "Next.js"], parent="react", domain="web", automation_risk_base=0.28),
    TaxonomySkill("nodejs",                 "tool",      ["node.js", "Node", "node"], domain="web", automation_risk_base=0.28),
    TaxonomySkill("flutter",                "tool",      ["Flutter", "dart"], domain="mobile", automation_risk_base=0.30),
    TaxonomySkill("react_native",           "tool",      ["react native", "RN"], parent="react", domain="mobile", automation_risk_base=0.32),

    # ── Blockchain / Web3 ─────────────────────────────
    TaxonomySkill("blockchain",             "technical", ["distributed ledger", "DLT"], domain="web3", automation_risk_base=0.18),
    TaxonomySkill("smart_contracts",        "technical", ["solidity", "smart contract development"], parent="blockchain", domain="web3", automation_risk_base=0.20),
    TaxonomySkill("defi",                   "domain",    ["decentralized finance", "DeFi"], parent="blockchain", domain="web3", automation_risk_base=0.22),

    # ── Quantum ───────────────────────────────────────
    TaxonomySkill("quantum_computing",      "technical", ["quantum", "qubits", "quantum algorithms"], domain="quantum", automation_risk_base=0.08),

    # ── Soft Skills ───────────────────────────────────
    TaxonomySkill("leadership",             "soft",      ["team leadership", "people management"], domain="soft", automation_risk_base=0.10),
    TaxonomySkill("communication",          "soft",      ["written communication", "verbal communication", "presentation"], domain="soft", automation_risk_base=0.12),
    TaxonomySkill("problem_solving",        "soft",      ["analytical thinking", "critical thinking"], domain="soft", automation_risk_base=0.15),
    TaxonomySkill("project_management",     "methodology", ["PM", "scrum master", "agile", "scrum"], domain="soft", automation_risk_base=0.35),

    # ── Emerging ──────────────────────────────────────
    TaxonomySkill("edge_computing",         "technical", ["edge AI", "IoT edge"], domain="emerging", automation_risk_base=0.20),
    TaxonomySkill("digital_twins",          "technical", ["digital twin", "simulation modeling"], domain="emerging", automation_risk_base=0.22),
    TaxonomySkill("robotics",              "technical", ["robot programming", "ROS"], domain="emerging", automation_risk_base=0.15),
    TaxonomySkill("ar_vr",                 "technical", ["augmented reality", "virtual reality", "XR", "mixed reality", "metaverse"], domain="emerging", automation_risk_base=0.20),

    # ── Industry-specific ─────────────────────────────
    TaxonomySkill("bioinformatics",         "domain",    ["computational biology", "genomics"], domain="healthcare", automation_risk_base=0.15),
    TaxonomySkill("fintech",                "domain",    ["financial technology"], domain="finance", automation_risk_base=0.22),
    TaxonomySkill("green_tech",             "domain",    ["sustainability tech", "clean tech", "cleantech"], domain="energy", automation_risk_base=0.18),
]
# fmt: on

# ── Relationship Ontology ──────────────────────────────────────────────────

SKILL_RELATIONSHIPS: List[Tuple[str, str, str, float]] = [
    # (source, target, relationship_type, weight)
    ("deep_learning", "machine_learning", "prerequisite", 0.9),
    ("natural_language_processing", "machine_learning", "prerequisite", 0.8),
    ("computer_vision", "deep_learning", "prerequisite", 0.85),
    ("generative_ai", "deep_learning", "prerequisite", 0.9),
    ("generative_ai", "natural_language_processing", "complementary", 0.8),
    ("prompt_engineering", "generative_ai", "prerequisite", 0.95),
    ("mlops", "machine_learning", "complementary", 0.85),
    ("mlops", "devops", "complementary", 0.7),
    ("data_science", "python", "prerequisite", 0.8),
    ("data_science", "sql", "prerequisite", 0.75),
    ("data_science", "machine_learning", "complementary", 0.85),
    ("data_engineering", "sql", "prerequisite", 0.9),
    ("data_engineering", "python", "prerequisite", 0.7),
    ("data_engineering", "big_data", "complementary", 0.8),
    ("kubernetes", "docker", "prerequisite", 0.9),
    ("devops", "docker", "complementary", 0.8),
    ("devops", "kubernetes", "complementary", 0.7),
    ("infrastructure_as_code", "cloud_computing", "complementary", 0.85),
    ("aws", "cloud_computing", "specialization", 0.95),
    ("azure", "cloud_computing", "specialization", 0.95),
    ("gcp", "cloud_computing", "specialization", 0.95),
    ("typescript", "javascript", "prerequisite", 0.9),
    ("nextjs", "react", "prerequisite", 0.95),
    ("react_native", "react", "prerequisite", 0.9),
    ("nodejs", "javascript", "prerequisite", 0.85),
    ("penetration_testing", "cybersecurity", "specialization", 0.9),
    ("zero_trust", "cybersecurity", "specialization", 0.85),
    ("devsecops", "devops", "complementary", 0.8),
    ("devsecops", "cybersecurity", "complementary", 0.8),
    ("smart_contracts", "blockchain", "specialization", 0.9),
    ("defi", "blockchain", "specialization", 0.85),
    ("defi", "fintech", "complementary", 0.7),
    ("edge_computing", "cloud_computing", "complementary", 0.6),
    ("digital_twins", "data_science", "complementary", 0.5),
    ("robotics", "computer_vision", "complementary", 0.6),
    ("robotics", "reinforcement_learning", "complementary", 0.7),
    ("ar_vr", "computer_vision", "complementary", 0.6),
    ("bioinformatics", "data_science", "complementary", 0.7),
    ("bioinformatics", "python", "prerequisite", 0.7),
]


# ── Domain Mappings ────────────────────────────────────────────────────────

DOMAIN_INDUSTRY_MAP: Dict[str, List[str]] = {
    "ai_ml": ["technology", "finance", "healthcare", "manufacturing"],
    "data": ["technology", "finance", "healthcare", "retail"],
    "cloud": ["technology", "finance", "government"],
    "security": ["technology", "finance", "government", "healthcare"],
    "web": ["technology", "retail", "education"],
    "mobile": ["technology", "retail"],
    "web3": ["finance", "technology"],
    "quantum": ["technology", "energy"],
    "emerging": ["technology", "manufacturing", "energy"],
    "healthcare": ["healthcare"],
    "finance": ["finance"],
    "energy": ["energy"],
    "programming": ["technology"],
    "soft": ["technology", "finance", "healthcare", "education", "government", "manufacturing", "retail", "energy"],
}


# ── Lookup Helpers ─────────────────────────────────────────────────────────

class SkillTaxonomyIndex:
    """Fast lookup index over the canonical taxonomy."""

    def __init__(self) -> None:
        self._by_canonical: Dict[str, TaxonomySkill] = {}
        self._alias_map: Dict[str, str] = {}  # lower-cased alias → canonical
        self._all_tokens: Set[str] = set()

        for sk in SKILL_TAXONOMY:
            self._by_canonical[sk.canonical] = sk
            self._alias_map[sk.canonical.lower()] = sk.canonical
            for alias in sk.aliases:
                self._alias_map[alias.lower()] = sk.canonical
            # Tokenised fragments for fuzzy matching
            for token in sk.canonical.replace("_", " ").split():
                self._all_tokens.add(token.lower())
            for alias in sk.aliases:
                for token in alias.lower().split():
                    self._all_tokens.add(token)

    # ── exact / alias resolution ────────────────────────
    def resolve(self, text: str) -> Optional[str]:
        """Return canonical name if *text* matches any alias exactly."""
        return self._alias_map.get(text.lower().strip())

    # ── fuzzy match ─────────────────────────────────────
    def fuzzy_match(self, text: str, threshold: float = 0.70) -> Optional[str]:
        """Return best canonical match above *threshold* similarity."""
        text_lower = text.lower().strip()
        # Try exact first
        exact = self.resolve(text_lower)
        if exact:
            return exact
        best_score, best_match = 0.0, None
        for alias, canon in self._alias_map.items():
            score = SequenceMatcher(None, text_lower, alias).ratio()
            if score > best_score:
                best_score = score
                best_match = canon
        return best_match if best_score >= threshold else None

    def get(self, canonical: str) -> Optional[TaxonomySkill]:
        return self._by_canonical.get(canonical)

    def all_skills(self) -> List[TaxonomySkill]:
        return list(self._by_canonical.values())

    def skills_by_domain(self, domain: str) -> List[TaxonomySkill]:
        return [s for s in self._by_canonical.values() if s.domain == domain]


# Singleton index
taxonomy_index = SkillTaxonomyIndex()
