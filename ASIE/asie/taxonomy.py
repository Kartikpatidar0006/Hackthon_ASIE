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

    # ── Finance domain skills ─────────────────────────
    TaxonomySkill("risk_management",        "domain",    ["risk analysis", "credit risk", "market risk", "risk modeling"], domain="finance", automation_risk_base=0.30),
    TaxonomySkill("quantitative_analysis",  "technical", ["quant", "quantitative finance", "stochastic modeling"], domain="finance", automation_risk_base=0.18),
    TaxonomySkill("regulatory_compliance",  "domain",    ["compliance", "KYC", "AML", "regulatory", "audit"], domain="finance", automation_risk_base=0.35),
    TaxonomySkill("financial_modeling",     "technical", ["valuation", "DCF", "financial analysis", "excel modeling"], domain="finance", automation_risk_base=0.32),
    TaxonomySkill("algorithmic_trading",    "technical", ["algo trading", "HFT", "trading systems"], domain="finance", automation_risk_base=0.20),

    # ── Healthcare domain skills ──────────────────────
    TaxonomySkill("clinical_research",      "domain",    ["clinical trials", "clinical data management", "GCP", "FDA regulations"], domain="healthcare", automation_risk_base=0.25),
    TaxonomySkill("health_informatics",     "domain",    ["healthcare IT", "EHR", "EMR", "HL7", "FHIR", "health data"], domain="healthcare", automation_risk_base=0.28),
    TaxonomySkill("medical_imaging",        "technical", ["radiology AI", "DICOM", "medical image analysis"], parent="computer_vision", domain="healthcare", automation_risk_base=0.12),
    TaxonomySkill("epidemiology",           "domain",    ["public health analytics", "disease modeling", "biostatistics"], domain="healthcare", automation_risk_base=0.18),

    # ── Manufacturing domain skills ───────────────────
    TaxonomySkill("supply_chain",           "domain",    ["supply chain management", "SCM", "logistics", "procurement"], domain="manufacturing", automation_risk_base=0.35),
    TaxonomySkill("quality_engineering",    "technical", ["quality assurance", "QA", "six sigma", "lean manufacturing"], domain="manufacturing", automation_risk_base=0.30),
    TaxonomySkill("industrial_iot",         "technical", ["IIoT", "industrial automation", "SCADA", "PLC programming"], domain="manufacturing", automation_risk_base=0.22),
    TaxonomySkill("cad_cam",               "tool",      ["CAD", "CAM", "SolidWorks", "AutoCAD", "3D modeling"], domain="manufacturing", automation_risk_base=0.30),

    # ── Energy domain skills ──────────────────────────
    TaxonomySkill("power_systems",          "domain",    ["electrical grid", "smart grid", "power engineering"], domain="energy", automation_risk_base=0.22),
    TaxonomySkill("renewable_energy",       "domain",    ["solar", "wind energy", "energy storage", "battery tech"], domain="energy", automation_risk_base=0.18),
    TaxonomySkill("energy_analytics",       "technical", ["energy data", "load forecasting", "energy optimization"], domain="energy", automation_risk_base=0.25),

    # ── Education domain skills ───────────────────────
    TaxonomySkill("instructional_design",   "domain",    ["curriculum design", "learning design", "course development"], domain="education", automation_risk_base=0.30),
    TaxonomySkill("edtech",                 "domain",    ["education technology", "LMS", "e-learning", "moodle"], domain="education", automation_risk_base=0.25),
    TaxonomySkill("learning_analytics",     "technical", ["student analytics", "educational data mining"], domain="education", automation_risk_base=0.28),

    # ── Retail domain skills ──────────────────────────
    TaxonomySkill("ecommerce",              "domain",    ["e-commerce", "online retail", "shopify", "magento"], domain="retail", automation_risk_base=0.30),
    TaxonomySkill("marketing_analytics",    "technical", ["digital marketing", "SEO", "SEM", "growth hacking", "marketing data"], domain="retail", automation_risk_base=0.32),
    TaxonomySkill("crm",                    "tool",      ["CRM", "salesforce", "HubSpot", "customer relationship"], domain="retail", automation_risk_base=0.35),
    TaxonomySkill("recommendation_systems", "technical", ["recommender", "personalization", "collaborative filtering"], parent="machine_learning", domain="retail", automation_risk_base=0.20),

    # ── Government domain skills ──────────────────────
    TaxonomySkill("govtech",                "domain",    ["government technology", "civic tech", "digital government"], domain="government", automation_risk_base=0.28),
    TaxonomySkill("policy_analysis",        "domain",    ["public policy", "policy research", "regulatory analysis"], domain="government", automation_risk_base=0.22),
    TaxonomySkill("geospatial_analysis",    "technical", ["GIS", "geospatial", "remote sensing", "mapping"], domain="government", automation_risk_base=0.25),
]
# fmt: on


# ── Job Role Skill Profiles (Industry → Roles → Skills) ───────────────────
# Each role belongs to one or more industries and defines weighted skill needs.
# Weights represent importance for the role (0-1), used as demand targets.

@dataclass
class JobRoleProfile:
    role_id: str
    display_name: str
    description: str
    industries: List[str]                   # which industries this role exists in
    required_skills: Dict[str, float]       # canonical_skill → importance (0-1)
    preferred_skills: Dict[str, float]      # nice-to-have skills
    trend_outlook: str = "stable"           # growing | stable | declining
    future_demand_multiplier: float = 1.0   # 3-5yr demand growth factor


JOB_ROLE_PROFILES: Dict[str, JobRoleProfile] = {

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TECHNOLOGY
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "software_engineer": JobRoleProfile(
        role_id="software_engineer",
        display_name="Software Engineer",
        description="Designs, builds & maintains scalable software systems",
        industries=["technology"],
        required_skills={
            "python": 0.80, "java": 0.70, "sql": 0.70, "devops": 0.55,
            "docker": 0.55, "problem_solving": 0.80, "communication": 0.60,
            "cloud_computing": 0.55,
        },
        preferred_skills={
            "typescript": 0.50, "golang": 0.45, "kubernetes": 0.45,
            "infrastructure_as_code": 0.40, "cybersecurity": 0.35,
        },
        trend_outlook="growing", future_demand_multiplier=1.15,
    ),

    "full_stack_developer": JobRoleProfile(
        role_id="full_stack_developer",
        display_name="Full Stack Web Developer",
        description="Builds end-to-end web apps — frontend, backend & database",
        industries=["technology"],
        required_skills={
            "javascript": 0.90, "typescript": 0.80, "react": 0.85,
            "nodejs": 0.80, "sql": 0.75, "python": 0.55,
            "docker": 0.50, "devops": 0.50, "problem_solving": 0.70,
        },
        preferred_skills={
            "nextjs": 0.60, "cloud_computing": 0.50, "aws": 0.45,
            "kubernetes": 0.35, "cybersecurity": 0.35, "communication": 0.50,
        },
        trend_outlook="growing", future_demand_multiplier=1.10,
    ),

    "ai_engineer": JobRoleProfile(
        role_id="ai_engineer",
        display_name="AI / ML Engineer",
        description="Builds & deploys AI/ML models into production systems",
        industries=["technology"],
        required_skills={
            "python": 0.95, "machine_learning": 0.90, "deep_learning": 0.80,
            "generative_ai": 0.75, "mlops": 0.70, "data_science": 0.65,
            "cloud_computing": 0.60, "docker": 0.55,
        },
        preferred_skills={
            "natural_language_processing": 0.65, "computer_vision": 0.55,
            "prompt_engineering": 0.60, "kubernetes": 0.45, "sql": 0.50,
            "big_data": 0.45, "reinforcement_learning": 0.40,
        },
        trend_outlook="growing", future_demand_multiplier=1.35,
    ),

    "data_scientist_tech": JobRoleProfile(
        role_id="data_scientist_tech",
        display_name="Data Scientist",
        description="Extracts insights & builds predictive models from data",
        industries=["technology"],
        required_skills={
            "python": 0.90, "data_science": 0.90, "machine_learning": 0.80,
            "sql": 0.80, "data_visualization": 0.70, "problem_solving": 0.80,
            "communication": 0.65,
        },
        preferred_skills={
            "deep_learning": 0.55, "big_data": 0.50,
            "natural_language_processing": 0.50, "cloud_computing": 0.45,
            "data_engineering": 0.50,
        },
        trend_outlook="growing", future_demand_multiplier=1.20,
    ),

    "data_engineer": JobRoleProfile(
        role_id="data_engineer",
        display_name="Data Engineer",
        description="Designs & maintains data pipelines and infrastructure",
        industries=["technology"],
        required_skills={
            "python": 0.85, "sql": 0.90, "data_engineering": 0.90,
            "big_data": 0.75, "cloud_computing": 0.70, "docker": 0.60,
            "devops": 0.55,
        },
        preferred_skills={
            "aws": 0.55, "kubernetes": 0.50, "data_science": 0.45,
            "machine_learning": 0.35, "infrastructure_as_code": 0.40,
        },
        trend_outlook="growing", future_demand_multiplier=1.25,
    ),

    "devops_engineer": JobRoleProfile(
        role_id="devops_engineer",
        display_name="DevOps / Platform Engineer",
        description="Automates infrastructure, CI/CD & deployment pipelines",
        industries=["technology"],
        required_skills={
            "devops": 0.90, "docker": 0.85, "kubernetes": 0.80,
            "cloud_computing": 0.85, "infrastructure_as_code": 0.75,
            "python": 0.60, "cybersecurity": 0.55,
        },
        preferred_skills={
            "aws": 0.65, "azure": 0.55, "golang": 0.50, "devsecops": 0.55,
            "problem_solving": 0.60, "communication": 0.45,
        },
        trend_outlook="growing", future_demand_multiplier=1.20,
    ),

    "cybersecurity_engineer": JobRoleProfile(
        role_id="cybersecurity_engineer",
        display_name="Cybersecurity Engineer",
        description="Protects systems & data from security threats",
        industries=["technology"],
        required_skills={
            "cybersecurity": 0.95, "penetration_testing": 0.75,
            "zero_trust": 0.65, "devsecops": 0.60, "cloud_computing": 0.60,
            "python": 0.55, "problem_solving": 0.80,
        },
        preferred_skills={
            "devops": 0.50, "docker": 0.45, "kubernetes": 0.40,
            "communication": 0.50, "leadership": 0.40,
        },
        trend_outlook="growing", future_demand_multiplier=1.30,
    ),

    "mobile_developer": JobRoleProfile(
        role_id="mobile_developer",
        display_name="Mobile App Developer",
        description="Builds native & cross-platform mobile applications",
        industries=["technology"],
        required_skills={
            "flutter": 0.80, "react_native": 0.75, "javascript": 0.70,
            "typescript": 0.60, "problem_solving": 0.70,
        },
        preferred_skills={
            "react": 0.50, "nodejs": 0.40, "cloud_computing": 0.35,
            "devops": 0.30, "cybersecurity": 0.30, "communication": 0.50,
        },
        trend_outlook="growing", future_demand_multiplier=1.10,
    ),

    "blockchain_developer": JobRoleProfile(
        role_id="blockchain_developer",
        display_name="Blockchain Developer",
        description="Builds decentralized applications & smart contracts",
        industries=["technology"],
        required_skills={
            "blockchain": 0.90, "smart_contracts": 0.85, "javascript": 0.70,
            "python": 0.55, "cybersecurity": 0.55, "problem_solving": 0.70,
        },
        preferred_skills={
            "defi": 0.60, "rust": 0.50, "golang": 0.45, "devops": 0.40,
            "cloud_computing": 0.35,
        },
        trend_outlook="stable", future_demand_multiplier=1.05,
    ),

    "product_manager_tech": JobRoleProfile(
        role_id="product_manager_tech",
        display_name="Product Manager",
        description="Defines product vision, roadmaps & drives cross-team delivery",
        industries=["technology"],
        required_skills={
            "project_management": 0.90, "communication": 0.90,
            "problem_solving": 0.85, "data_visualization": 0.60,
            "leadership": 0.75, "data_science": 0.45,
        },
        preferred_skills={
            "sql": 0.40, "python": 0.30, "machine_learning": 0.25,
        },
        trend_outlook="growing", future_demand_multiplier=1.15,
    ),

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FINANCE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "quantitative_analyst": JobRoleProfile(
        role_id="quantitative_analyst",
        display_name="Quantitative Analyst",
        description="Develops mathematical models for pricing, risk & trading strategies",
        industries=["finance"],
        required_skills={
            "quantitative_analysis": 0.95, "python": 0.85,
            "financial_modeling": 0.80, "machine_learning": 0.65,
            "data_science": 0.70, "problem_solving": 0.90,
        },
        preferred_skills={
            "algorithmic_trading": 0.55, "deep_learning": 0.40,
            "big_data": 0.40, "sql": 0.50, "cpp": 0.45,
        },
        trend_outlook="growing", future_demand_multiplier=1.25,
    ),

    "risk_analyst": JobRoleProfile(
        role_id="risk_analyst",
        display_name="Risk Analyst / Manager",
        description="Identifies, models & mitigates financial risks across the organisation",
        industries=["finance"],
        required_skills={
            "risk_management": 0.95, "financial_modeling": 0.80,
            "data_science": 0.65, "sql": 0.70,
            "regulatory_compliance": 0.60, "problem_solving": 0.80,
            "communication": 0.70,
        },
        preferred_skills={
            "python": 0.55, "machine_learning": 0.45,
            "data_visualization": 0.50, "leadership": 0.40,
        },
        trend_outlook="growing", future_demand_multiplier=1.20,
    ),

    "fintech_developer": JobRoleProfile(
        role_id="fintech_developer",
        display_name="Fintech Developer",
        description="Builds digital payment, lending & banking technology platforms",
        industries=["finance"],
        required_skills={
            "fintech": 0.85, "python": 0.80, "javascript": 0.70,
            "sql": 0.75, "cybersecurity": 0.65, "cloud_computing": 0.60,
            "devops": 0.50,
        },
        preferred_skills={
            "blockchain": 0.45, "docker": 0.45, "react": 0.40,
            "regulatory_compliance": 0.40, "problem_solving": 0.60,
        },
        trend_outlook="growing", future_demand_multiplier=1.25,
    ),

    "compliance_officer": JobRoleProfile(
        role_id="compliance_officer",
        display_name="Compliance Officer / Analyst",
        description="Ensures regulatory adherence — KYC, AML, audit & governance",
        industries=["finance"],
        required_skills={
            "regulatory_compliance": 0.95, "risk_management": 0.70,
            "communication": 0.80, "problem_solving": 0.70,
            "leadership": 0.55, "project_management": 0.55,
        },
        preferred_skills={
            "data_science": 0.35, "sql": 0.40, "python": 0.30,
            "data_visualization": 0.35,
        },
        trend_outlook="growing", future_demand_multiplier=1.15,
    ),

    "algo_trader": JobRoleProfile(
        role_id="algo_trader",
        display_name="Algorithmic Trader / Developer",
        description="Designs & implements automated trading strategies & systems",
        industries=["finance"],
        required_skills={
            "algorithmic_trading": 0.95, "python": 0.90,
            "quantitative_analysis": 0.80, "machine_learning": 0.65,
            "data_engineering": 0.55, "problem_solving": 0.85,
        },
        preferred_skills={
            "cpp": 0.55, "big_data": 0.45, "cloud_computing": 0.40,
            "deep_learning": 0.40, "rust": 0.35,
        },
        trend_outlook="growing", future_demand_multiplier=1.20,
    ),

    "financial_data_analyst": JobRoleProfile(
        role_id="financial_data_analyst",
        display_name="Financial Data Analyst",
        description="Analyses financial data for reporting, forecasting & decision support",
        industries=["finance"],
        required_skills={
            "financial_modeling": 0.85, "sql": 0.85,
            "data_visualization": 0.80, "data_science": 0.65,
            "communication": 0.75, "problem_solving": 0.70,
        },
        preferred_skills={
            "python": 0.50, "machine_learning": 0.35,
            "risk_management": 0.40, "big_data": 0.35,
        },
        trend_outlook="growing", future_demand_multiplier=1.15,
    ),

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # HEALTHCARE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "bioinformatics_engineer": JobRoleProfile(
        role_id="bioinformatics_engineer",
        display_name="Bioinformatics Engineer",
        description="Applies computational methods to biological & genomic data",
        industries=["healthcare"],
        required_skills={
            "bioinformatics": 0.90, "python": 0.85, "data_science": 0.75,
            "machine_learning": 0.60, "sql": 0.65, "problem_solving": 0.75,
        },
        preferred_skills={
            "cloud_computing": 0.45, "big_data": 0.50, "deep_learning": 0.40,
            "data_engineering": 0.40,
        },
        trend_outlook="growing", future_demand_multiplier=1.25,
    ),

    "health_informatics_specialist": JobRoleProfile(
        role_id="health_informatics_specialist",
        display_name="Health Informatics Specialist",
        description="Manages EHR/EMR systems, HL7/FHIR interoperability & health IT",
        industries=["healthcare"],
        required_skills={
            "health_informatics": 0.95, "sql": 0.75,
            "data_visualization": 0.60, "cybersecurity": 0.55,
            "communication": 0.70, "problem_solving": 0.65,
        },
        preferred_skills={
            "python": 0.40, "cloud_computing": 0.45, "data_science": 0.40,
            "project_management": 0.45, "machine_learning": 0.30,
        },
        trend_outlook="growing", future_demand_multiplier=1.20,
    ),

    "clinical_data_manager": JobRoleProfile(
        role_id="clinical_data_manager",
        display_name="Clinical Data Manager",
        description="Manages clinical trial data, ensures GCP compliance & data quality",
        industries=["healthcare"],
        required_skills={
            "clinical_research": 0.90, "sql": 0.80,
            "data_science": 0.55, "regulatory_compliance": 0.60,
            "communication": 0.70, "problem_solving": 0.65,
        },
        preferred_skills={
            "python": 0.40, "data_visualization": 0.45,
            "project_management": 0.50, "health_informatics": 0.40,
        },
        trend_outlook="growing", future_demand_multiplier=1.15,
    ),

    "medical_ai_researcher": JobRoleProfile(
        role_id="medical_ai_researcher",
        display_name="Medical AI / Imaging Researcher",
        description="Builds AI models for medical imaging, diagnostics & drug discovery",
        industries=["healthcare"],
        required_skills={
            "medical_imaging": 0.85, "deep_learning": 0.85,
            "python": 0.85, "machine_learning": 0.80,
            "computer_vision": 0.75, "problem_solving": 0.80,
        },
        preferred_skills={
            "bioinformatics": 0.45, "data_science": 0.50,
            "cloud_computing": 0.40, "mlops": 0.40,
        },
        trend_outlook="growing", future_demand_multiplier=1.35,
    ),

    "epidemiologist": JobRoleProfile(
        role_id="epidemiologist",
        display_name="Epidemiologist / Public Health Analyst",
        description="Analyses disease patterns, models outbreaks & guides health policy",
        industries=["healthcare"],
        required_skills={
            "epidemiology": 0.90, "data_science": 0.75,
            "python": 0.60, "data_visualization": 0.65,
            "communication": 0.75, "problem_solving": 0.80,
        },
        preferred_skills={
            "machine_learning": 0.40, "sql": 0.50,
            "geospatial_analysis": 0.40, "big_data": 0.35,
        },
        trend_outlook="growing", future_demand_multiplier=1.20,
    ),

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # MANUFACTURING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "industrial_iot_engineer": JobRoleProfile(
        role_id="industrial_iot_engineer",
        display_name="Industrial IoT Engineer",
        description="Connects factory equipment, builds SCADA/PLC based automation systems",
        industries=["manufacturing"],
        required_skills={
            "industrial_iot": 0.90, "python": 0.65,
            "edge_computing": 0.70, "cloud_computing": 0.55,
            "cybersecurity": 0.50, "problem_solving": 0.75,
        },
        preferred_skills={
            "data_science": 0.40, "digital_twins": 0.50,
            "machine_learning": 0.35, "docker": 0.35,
        },
        trend_outlook="growing", future_demand_multiplier=1.25,
    ),

    "supply_chain_analyst": JobRoleProfile(
        role_id="supply_chain_analyst",
        display_name="Supply Chain Analyst",
        description="Optimises procurement, logistics & inventory using data analytics",
        industries=["manufacturing"],
        required_skills={
            "supply_chain": 0.90, "data_science": 0.65, "sql": 0.70,
            "data_visualization": 0.65, "problem_solving": 0.75,
            "communication": 0.65,
        },
        preferred_skills={
            "python": 0.45, "machine_learning": 0.40,
            "project_management": 0.50, "big_data": 0.35,
        },
        trend_outlook="growing", future_demand_multiplier=1.15,
    ),

    "quality_engineer": JobRoleProfile(
        role_id="quality_engineer",
        display_name="Quality / Six Sigma Engineer",
        description="Ensures manufacturing quality standards using data & lean processes",
        industries=["manufacturing"],
        required_skills={
            "quality_engineering": 0.90, "data_visualization": 0.60,
            "data_science": 0.50, "problem_solving": 0.80,
            "communication": 0.65, "project_management": 0.60,
        },
        preferred_skills={
            "python": 0.35, "sql": 0.45, "machine_learning": 0.30,
            "industrial_iot": 0.35, "supply_chain": 0.35,
        },
        trend_outlook="stable", future_demand_multiplier=1.05,
    ),

    "digital_twin_engineer": JobRoleProfile(
        role_id="digital_twin_engineer",
        display_name="Digital Twin Engineer",
        description="Creates virtual replicas of physical systems for simulation & optimization",
        industries=["manufacturing"],
        required_skills={
            "digital_twins": 0.90, "python": 0.70, "data_science": 0.65,
            "cloud_computing": 0.55, "cad_cam": 0.50, "problem_solving": 0.75,
        },
        preferred_skills={
            "machine_learning": 0.45, "industrial_iot": 0.50,
            "edge_computing": 0.40, "big_data": 0.35,
        },
        trend_outlook="growing", future_demand_multiplier=1.30,
    ),

    "robotics_engineer": JobRoleProfile(
        role_id="robotics_engineer",
        display_name="Robotics Engineer",
        description="Designs & programs autonomous robotic systems",
        industries=["manufacturing"],
        required_skills={
            "robotics": 0.90, "python": 0.80, "computer_vision": 0.70,
            "reinforcement_learning": 0.65, "cpp": 0.60,
            "problem_solving": 0.80,
        },
        preferred_skills={
            "deep_learning": 0.55, "edge_computing": 0.50,
            "cloud_computing": 0.40, "docker": 0.35,
        },
        trend_outlook="growing", future_demand_multiplier=1.20,
    ),

    "manufacturing_automation": JobRoleProfile(
        role_id="manufacturing_automation",
        display_name="Automation / Controls Engineer",
        description="Designs automation solutions, PLC programming & process control",
        industries=["manufacturing"],
        required_skills={
            "industrial_iot": 0.80, "cad_cam": 0.70, "cpp": 0.55,
            "problem_solving": 0.80, "quality_engineering": 0.50,
            "project_management": 0.55,
        },
        preferred_skills={
            "python": 0.40, "robotics": 0.50, "edge_computing": 0.40,
            "digital_twins": 0.35, "communication": 0.50,
        },
        trend_outlook="growing", future_demand_multiplier=1.20,
    ),

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ENERGY
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "green_tech_engineer": JobRoleProfile(
        role_id="green_tech_engineer",
        display_name="Green Tech / Sustainability Engineer",
        description="Develops sustainable technology solutions for cleaner energy",
        industries=["energy"],
        required_skills={
            "green_tech": 0.90, "renewable_energy": 0.75,
            "data_science": 0.60, "python": 0.55,
            "problem_solving": 0.70, "project_management": 0.55,
        },
        preferred_skills={
            "cloud_computing": 0.40, "edge_computing": 0.45,
            "machine_learning": 0.40, "communication": 0.50,
        },
        trend_outlook="growing", future_demand_multiplier=1.30,
    ),

    "energy_data_analyst": JobRoleProfile(
        role_id="energy_data_analyst",
        display_name="Energy Data Analyst",
        description="Analyses consumption patterns, forecasts load & optimises energy usage",
        industries=["energy"],
        required_skills={
            "energy_analytics": 0.90, "data_science": 0.75,
            "python": 0.70, "data_visualization": 0.70,
            "sql": 0.65, "problem_solving": 0.70,
        },
        preferred_skills={
            "machine_learning": 0.50, "big_data": 0.40,
            "power_systems": 0.40, "communication": 0.50,
        },
        trend_outlook="growing", future_demand_multiplier=1.25,
    ),

    "power_systems_engineer": JobRoleProfile(
        role_id="power_systems_engineer",
        display_name="Power Systems / Smart Grid Engineer",
        description="Designs, operates & modernises electrical grids & power infrastructure",
        industries=["energy"],
        required_skills={
            "power_systems": 0.90, "renewable_energy": 0.65,
            "problem_solving": 0.80, "project_management": 0.60,
            "communication": 0.60, "python": 0.45,
        },
        preferred_skills={
            "industrial_iot": 0.45, "edge_computing": 0.40,
            "energy_analytics": 0.50, "digital_twins": 0.35,
            "machine_learning": 0.30,
        },
        trend_outlook="growing", future_demand_multiplier=1.20,
    ),

    "renewable_energy_specialist": JobRoleProfile(
        role_id="renewable_energy_specialist",
        display_name="Renewable Energy Specialist",
        description="Plans & implements solar, wind & battery storage projects",
        industries=["energy"],
        required_skills={
            "renewable_energy": 0.95, "green_tech": 0.70,
            "project_management": 0.75, "communication": 0.65,
            "problem_solving": 0.70, "data_visualization": 0.45,
        },
        preferred_skills={
            "energy_analytics": 0.45, "python": 0.35,
            "power_systems": 0.50, "leadership": 0.45,
        },
        trend_outlook="growing", future_demand_multiplier=1.35,
    ),

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # EDUCATION
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "edtech_developer": JobRoleProfile(
        role_id="edtech_developer",
        display_name="EdTech Developer",
        description="Builds e-learning platforms, LMS & educational software tools",
        industries=["education"],
        required_skills={
            "edtech": 0.85, "javascript": 0.75, "react": 0.65,
            "python": 0.55, "sql": 0.60, "problem_solving": 0.70,
        },
        preferred_skills={
            "nodejs": 0.50, "cloud_computing": 0.40,
            "generative_ai": 0.40, "docker": 0.30,
            "communication": 0.50,
        },
        trend_outlook="growing", future_demand_multiplier=1.25,
    ),

    "instructional_designer": JobRoleProfile(
        role_id="instructional_designer",
        display_name="Instructional Designer",
        description="Designs curricula, learning experiences & course content strategies",
        industries=["education"],
        required_skills={
            "instructional_design": 0.95, "communication": 0.85,
            "edtech": 0.60, "problem_solving": 0.65,
            "project_management": 0.60, "data_visualization": 0.40,
        },
        preferred_skills={
            "learning_analytics": 0.45, "generative_ai": 0.35,
            "python": 0.20, "leadership": 0.40,
        },
        trend_outlook="growing", future_demand_multiplier=1.15,
    ),

    "learning_analytics_specialist": JobRoleProfile(
        role_id="learning_analytics_specialist",
        display_name="Learning Analytics Specialist",
        description="Analyses student performance data to improve learning outcomes",
        industries=["education"],
        required_skills={
            "learning_analytics": 0.90, "data_science": 0.75,
            "sql": 0.70, "data_visualization": 0.70,
            "python": 0.60, "communication": 0.65,
        },
        preferred_skills={
            "machine_learning": 0.45, "edtech": 0.40,
            "instructional_design": 0.35, "big_data": 0.30,
        },
        trend_outlook="growing", future_demand_multiplier=1.20,
    ),

    "education_ai_specialist": JobRoleProfile(
        role_id="education_ai_specialist",
        display_name="AI in Education Specialist",
        description="Applies AI & GenAI for personalised tutoring, grading & content generation",
        industries=["education"],
        required_skills={
            "generative_ai": 0.80, "machine_learning": 0.70,
            "python": 0.75, "natural_language_processing": 0.65,
            "edtech": 0.55, "problem_solving": 0.70,
        },
        preferred_skills={
            "prompt_engineering": 0.55, "deep_learning": 0.45,
            "learning_analytics": 0.40, "communication": 0.50,
        },
        trend_outlook="growing", future_demand_multiplier=1.35,
    ),

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # RETAIL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "ecommerce_developer": JobRoleProfile(
        role_id="ecommerce_developer",
        display_name="E-Commerce Developer",
        description="Builds & maintains online storefronts, payment & inventory systems",
        industries=["retail"],
        required_skills={
            "ecommerce": 0.90, "javascript": 0.80, "react": 0.65,
            "nodejs": 0.60, "sql": 0.70, "python": 0.45,
        },
        preferred_skills={
            "cloud_computing": 0.45, "docker": 0.35, "devops": 0.35,
            "cybersecurity": 0.35, "communication": 0.45,
        },
        trend_outlook="growing", future_demand_multiplier=1.15,
    ),

    "marketing_analyst": JobRoleProfile(
        role_id="marketing_analyst",
        display_name="Marketing / Growth Analyst",
        description="Drives growth via SEO/SEM, campaign analytics & customer insights",
        industries=["retail"],
        required_skills={
            "marketing_analytics": 0.90, "data_visualization": 0.75,
            "sql": 0.65, "communication": 0.80,
            "problem_solving": 0.65, "crm": 0.55,
        },
        preferred_skills={
            "python": 0.40, "data_science": 0.45,
            "machine_learning": 0.30, "ecommerce": 0.40,
        },
        trend_outlook="growing", future_demand_multiplier=1.15,
    ),

    "recommendation_engineer": JobRoleProfile(
        role_id="recommendation_engineer",
        display_name="Recommendation / Personalisation Engineer",
        description="Builds ML-powered recommendation engines for products & content",
        industries=["retail"],
        required_skills={
            "recommendation_systems": 0.90, "machine_learning": 0.85,
            "python": 0.85, "data_science": 0.70,
            "sql": 0.65, "problem_solving": 0.75,
        },
        preferred_skills={
            "deep_learning": 0.50, "big_data": 0.50,
            "cloud_computing": 0.40, "data_engineering": 0.45,
        },
        trend_outlook="growing", future_demand_multiplier=1.25,
    ),

    "crm_specialist": JobRoleProfile(
        role_id="crm_specialist",
        display_name="CRM / Customer Success Analyst",
        description="Manages customer relationships, retention analytics & loyalty programs",
        industries=["retail"],
        required_skills={
            "crm": 0.90, "communication": 0.80, "sql": 0.60,
            "data_visualization": 0.60, "marketing_analytics": 0.55,
            "problem_solving": 0.60,
        },
        preferred_skills={
            "python": 0.30, "data_science": 0.35, "ecommerce": 0.40,
            "project_management": 0.40, "leadership": 0.35,
        },
        trend_outlook="stable", future_demand_multiplier=1.10,
    ),

    "retail_data_scientist": JobRoleProfile(
        role_id="retail_data_scientist",
        display_name="Retail Data Scientist",
        description="Applies ML for demand forecasting, pricing & customer segmentation",
        industries=["retail"],
        required_skills={
            "data_science": 0.90, "python": 0.85, "machine_learning": 0.75,
            "sql": 0.75, "data_visualization": 0.65,
            "problem_solving": 0.75,
        },
        preferred_skills={
            "recommendation_systems": 0.50, "big_data": 0.45,
            "deep_learning": 0.40, "ecommerce": 0.35,
            "communication": 0.55,
        },
        trend_outlook="growing", future_demand_multiplier=1.20,
    ),

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # GOVERNMENT
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "govtech_developer": JobRoleProfile(
        role_id="govtech_developer",
        display_name="GovTech / Civic Tech Developer",
        description="Builds digital government platforms, portals & citizen services",
        industries=["government"],
        required_skills={
            "govtech": 0.85, "python": 0.65, "javascript": 0.60,
            "sql": 0.65, "cybersecurity": 0.60,
            "cloud_computing": 0.55,
        },
        preferred_skills={
            "react": 0.40, "devops": 0.40, "docker": 0.35,
            "communication": 0.50, "project_management": 0.45,
        },
        trend_outlook="growing", future_demand_multiplier=1.20,
    ),

    "policy_data_analyst": JobRoleProfile(
        role_id="policy_data_analyst",
        display_name="Policy / Data Analyst",
        description="Uses data to inform public policy, budgeting & governmental decisions",
        industries=["government"],
        required_skills={
            "policy_analysis": 0.85, "data_science": 0.75,
            "data_visualization": 0.75, "sql": 0.65,
            "communication": 0.80, "problem_solving": 0.70,
        },
        preferred_skills={
            "python": 0.50, "machine_learning": 0.35,
            "geospatial_analysis": 0.40, "big_data": 0.30,
        },
        trend_outlook="growing", future_demand_multiplier=1.15,
    ),

    "gov_cybersecurity": JobRoleProfile(
        role_id="gov_cybersecurity",
        display_name="Government Cybersecurity Specialist",
        description="Secures critical government infrastructure, networks & citizen data",
        industries=["government"],
        required_skills={
            "cybersecurity": 0.95, "zero_trust": 0.70,
            "cloud_computing": 0.60, "devsecops": 0.55,
            "problem_solving": 0.80, "communication": 0.60,
        },
        preferred_skills={
            "python": 0.50, "penetration_testing": 0.55,
            "devops": 0.40, "govtech": 0.35, "leadership": 0.45,
        },
        trend_outlook="growing", future_demand_multiplier=1.30,
    ),

    "geospatial_analyst": JobRoleProfile(
        role_id="geospatial_analyst",
        display_name="Geospatial / GIS Analyst",
        description="Analyses location data for urban planning, defense & resource management",
        industries=["government"],
        required_skills={
            "geospatial_analysis": 0.90, "data_visualization": 0.70,
            "python": 0.60, "sql": 0.60,
            "problem_solving": 0.70, "communication": 0.60,
        },
        preferred_skills={
            "machine_learning": 0.40, "data_science": 0.50,
            "cloud_computing": 0.35, "big_data": 0.30,
        },
        trend_outlook="growing", future_demand_multiplier=1.15,
    ),

    "digital_services_manager": JobRoleProfile(
        role_id="digital_services_manager",
        display_name="Digital Services / e-Gov Manager",
        description="Leads digital transformation of government services & citizen portals",
        industries=["government"],
        required_skills={
            "govtech": 0.80, "project_management": 0.85,
            "communication": 0.85, "leadership": 0.80,
            "cybersecurity": 0.50, "problem_solving": 0.70,
        },
        preferred_skills={
            "cloud_computing": 0.40, "data_visualization": 0.35,
            "policy_analysis": 0.40, "devops": 0.30,
        },
        trend_outlook="growing", future_demand_multiplier=1.20,
    ),
}


def get_roles_for_industry(industry: str) -> List[JobRoleProfile]:
    """Return all job roles relevant to a given industry."""
    return [p for p in JOB_ROLE_PROFILES.values() if industry in p.industries]


def get_role_demand_profile(role_id: str) -> Optional[Dict[str, float]]:
    """Get combined demand profile (required + preferred) for a job role."""
    profile = JOB_ROLE_PROFILES.get(role_id)
    if not profile:
        return None
    combined = dict(profile.required_skills)
    combined.update(profile.preferred_skills)
    return combined


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
    # Finance
    ("quantitative_analysis", "python", "prerequisite", 0.8),
    ("quantitative_analysis", "machine_learning", "complementary", 0.7),
    ("algorithmic_trading", "quantitative_analysis", "prerequisite", 0.9),
    ("algorithmic_trading", "python", "prerequisite", 0.8),
    ("financial_modeling", "data_science", "complementary", 0.6),
    ("risk_management", "financial_modeling", "complementary", 0.7),
    ("regulatory_compliance", "risk_management", "complementary", 0.6),
    # Healthcare
    ("medical_imaging", "deep_learning", "prerequisite", 0.85),
    ("health_informatics", "sql", "prerequisite", 0.7),
    ("clinical_research", "data_science", "complementary", 0.6),
    ("epidemiology", "data_science", "complementary", 0.75),
    # Manufacturing
    ("industrial_iot", "edge_computing", "complementary", 0.8),
    ("supply_chain", "data_science", "complementary", 0.5),
    ("quality_engineering", "data_visualization", "complementary", 0.5),
    ("digital_twins", "industrial_iot", "complementary", 0.7),
    # Energy
    ("renewable_energy", "green_tech", "complementary", 0.85),
    ("energy_analytics", "data_science", "prerequisite", 0.7),
    ("power_systems", "energy_analytics", "complementary", 0.6),
    # Education
    ("learning_analytics", "data_science", "prerequisite", 0.7),
    ("edtech", "instructional_design", "complementary", 0.8),
    # Retail
    ("recommendation_systems", "machine_learning", "prerequisite", 0.85),
    ("ecommerce", "marketing_analytics", "complementary", 0.7),
    ("marketing_analytics", "data_science", "complementary", 0.6),
    # Government
    ("geospatial_analysis", "data_visualization", "complementary", 0.6),
    ("govtech", "cybersecurity", "complementary", 0.6),
    ("policy_analysis", "data_science", "complementary", 0.5),
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
    "finance": ["finance", "technology"],
    "energy": ["energy", "manufacturing"],
    "manufacturing": ["manufacturing", "technology"],
    "education": ["education", "technology"],
    "retail": ["retail", "technology"],
    "government": ["government", "technology"],
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
