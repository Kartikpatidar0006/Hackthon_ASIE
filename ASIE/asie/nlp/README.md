# `asie/nlp/` — NLP Skill Extraction Engine

> Extracts and maps skill mentions from unstructured text to the canonical taxonomy.

## Overview

The NLP module is responsible for identifying skill mentions in free-form text (job descriptions, patent abstracts, research papers, resumes) and mapping them to ASIE's canonical skill taxonomy of 70+ skills with 200+ aliases.

## Files

| File | Purpose |
|---|---|
| `__init__.py` | `SkillExtractor` class + module-level `skill_extractor` singleton |

## Extraction Pipeline

```
Raw Text
    │
    ▼
┌────────────────────────┐
│  Phase 1: Exact Match  │  Pre-compiled regex patterns for all
│  (200+ alias patterns) │  canonical names + aliases
└──────────┬─────────────┘
           ▼
┌────────────────────────┐
│  Phase 2: Fuzzy Match  │  N-gram extraction + SequenceMatcher
│  (threshold ≥ 0.75)    │  for catching typos/variants
└──────────┬─────────────┘
           ▼
   Deduplicated canonical skill list
   (ordered by first appearance)
```

## Key Features

### 1. Pattern-Based Extraction (`extract()`)
- Pre-compiles regex patterns from all taxonomy entries at startup
- Word-boundary matching, case-insensitive
- Handles canonical names, hyphenated variants, and all aliases
- Returns deduplicated list of canonical skill identifiers

### 2. Confidence-Scored Extraction (`extract_with_confidence()`)
- Exact matches → confidence 0.9+ (boosted by frequency)
- Fuzzy matches → confidence proportional to SequenceMatcher ratio
- Frequency boost: more mentions = higher confidence (capped at 1.0)
- Returns `List[Tuple[str, float]]` sorted by confidence descending

### 3. Resume-Specific Extraction (`extract_from_resume()`)
- Estimates **proficiency level** (0–1) per detected skill
- Factors:
  - **Match confidence** — how clearly the skill was mentioned
  - **Context keywords** — "expert", "senior", "lead" → higher proficiency; "basic", "beginner" → lower
  - **Frequency of mention** — mentioned 5 times > mentioned once
  - **Proximity analysis** — checks 50 characters around the skill mention for context clues
- Returns `Dict[str, float]` of `{skill_id: proficiency_level}`

## Proficiency Context Keywords

| Level | Keywords | Proficiency Range |
|---|---|---|
| **Expert** | expert, advanced, senior, lead, architect, principal, mastery, proficient | 0.75 – 1.0 |
| **Intermediate** | intermediate, experienced, familiar, working knowledge, comfortable | 0.55 – 0.85 |
| **Beginner** | beginner, basic, learning, exposure, introductory, fundamentals | 0.30 – 0.50 |
| **Unspecified** | (no context keywords found) | 0.45 – 0.75 |

## Fuzzy Matching

When exact patterns don't match, the extractor falls back to fuzzy matching:
- Extracts unigrams, bigrams, and trigrams from the text
- Compares each n-gram against all canonical names and aliases using `difflib.SequenceMatcher`
- Threshold: **0.75** (configurable via `fuzzy_threshold`)
- Example: "machin learning" → `machine_learning` (ratio ≈ 0.93)

## Usage

```python
from asie.nlp import skill_extractor

# Basic extraction
skills = skill_extractor.extract(
    "Looking for Python developer with AWS and machine learning experience"
)
# → ["python", "aws", "machine_learning"]

# With confidence scores
results = skill_extractor.extract_with_confidence(
    "Expert in deep learning and computer vision"
)
# → [("deep_learning", 0.95), ("computer_vision", 0.92)]

# Resume analysis
proficiency = skill_extractor.extract_from_resume(
    "Senior Python engineer. Basic knowledge of Docker."
)
# → {"python": 0.85, "docker": 0.45}
```

## Production Roadmap

| Prototype (Current) | Production (Future) |
|---|---|
| Regex pattern matching | spaCy custom NER model |
| SequenceMatcher fuzzy | Fine-tuned BERT skill classifier |
| Rule-based proficiency | LLM-based contextual understanding |
| Static taxonomy | Dynamic taxonomy with auto-discovery |
