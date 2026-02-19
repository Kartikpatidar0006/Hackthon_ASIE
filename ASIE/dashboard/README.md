# `dashboard/` — React Interactive Dashboard

> Real-time skill intelligence visualization built with React 18, Recharts, and Vite.

## Overview

The dashboard is a single-page React application that consumes the ASIE REST API and renders interactive charts, tables, and analysis tools across 5 tabs. It features a editorial/newspaper-inspired design with green accent theming.

## Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| **React** | 18.2 | UI framework |
| **Recharts** | 2.10 | Chart library (Bar, Line, Area, Radar, Pie charts) |
| **Vite** | 5.0 | Build tool + dev server |
| **Tailwind CSS** | 3.4 | Utility-first CSS framework |
| **lucide-react** | 0.294 | Icon library |

## Project Structure

```
dashboard/
├── index.html              # HTML entry point
├── package.json            # Dependencies and scripts
├── vite.config.js          # Vite config (proxy /api → localhost:8000)
├── tailwind.config.js      # Tailwind configuration
├── postcss.config.js       # PostCSS configuration
└── src/
    ├── main.jsx            # React DOM mount point
    ├── App.jsx             # Full application (all components + tabs)
    ├── api.js              # API client (fetch wrapper for all endpoints)
    └── index.css           # Global styles / Tailwind imports
```

## Quick Start

```bash
# Install dependencies
cd dashboard
npm install

# Start dev server (proxies API calls to localhost:8000)
npm run dev
# → Opens at http://localhost:3000

# Production build
npm run build
# → Output: dashboard/dist/
```

> **Note:** The backend API must be running on port 8000 for the dashboard to load data.

## Dashboard Tabs

### Tab 1: Overview — Market Intelligence
- **4 KPI cards:** Skills Tracked, Avg Growth Score, Avg Automation Risk, Active Alerts
- **Top Growing Skills** — horizontal bar chart (growth score %)
- **Highest Risk Skills** — horizontal bar chart (automation risk %)
- **Alert Feed** — recent signals with type/severity badges
- **Trending** — skills ranked by momentum index
- **Emerging** — skills ranked by emergence score

### Tab 2: Forecast — Demand Prediction Engine
- **Skill selector** dropdown (all tracked skills)
- **6 KPI scores** — Growth, Confidence, Volatility, Momentum, Bubble, Automation Risk
- **5-Year Demand Curve** — area chart with prediction intervals (upper/lower bounds)
- **Skill Health Radar** — hexagonal radar chart (6 dimensions)
- **SHAP Feature Impact** — horizontal score bars showing which factors drive the prediction
- **Narrative explanation** — auto-generated human-readable summary

### Tab 3: Skills — Full Intelligence Registry
- **Sortable, searchable table** of all 70+ skills
- **8 columns:** Name, Category, Growth, Confidence, Volatility, Momentum, Bubble, Automation Risk
- **Color-coded** values (green = good, amber = caution, red = risky)
- **Category badges** — AI/ML, Cloud, DevOps, Security, etc.

### Tab 4: Resume — Gap Analyzer
- **Resume text input** with privacy notice
- **Industry selector** (8 industries)
- **Role selector** (dynamic, filtered by industry)
- **Results:** Skills Found, Readiness Score, Gaps Found, Recommended count
- **Skill Gaps** — priority-ordered with gap score bars (critical/high/medium/low)
- **Role Fit** — best-matching roles with readiness scores + missing skills
- **Industry Fit** — bar chart across 8 industries
- **Learning Roadmap** — recommended next skills as badges

### Tab 5: Alerts — Intelligence Monitoring
- **Full alert list** with type/severity badges and messages
- **Distribution pie chart** — alerts by type
- **Severity bar chart** — Critical, High, Medium, Low counts

## API Client (`src/api.js`)

All API calls go through the `api` object:

```javascript
api.getSummary()                    // GET /api/v1/dashboard/summary
api.getSkills(params)               // GET /api/v1/skills
api.getSkillForecast(id)            // GET /api/v1/skills/{id}/forecast
api.getTrending(limit)              // GET /api/v1/skills/trending
api.getEmerging(limit)              // GET /api/v1/skills/emerging
api.getAlerts(params)               // GET /api/v1/alerts
api.getGraph()                      // GET /api/v1/graph
api.getNeighbors(id, depth)         // GET /api/v1/graph/neighbors/{id}
api.getLearningPath(from, to)       // GET /api/v1/graph/learning-path
api.getRoles(industry)              // GET /api/v1/roles
api.analyzeResume(body)             // POST /api/v1/resume/analyze
```

Vite proxies all `/api` requests to `http://localhost:8000` during development.

## Design System

| Element | Value |
|---|---|
| **Primary Font** | Syne (headings, nav) |
| **Body Font** | Fraunces (narrative text) |
| **Mono Font** | IBM Plex Mono (labels, numbers, badges) |
| **Primary Color** | `#16a34a` (green-600) |
| **Dark BG** | `#0f2218` (header/footer) |
| **Accent Colors** | Teal `#0d9488`, Gold `#ca8a04`, Red `#dc2626`, Blue `#2563eb` |
| **Border Radius** | 8px (panels), 4px (inputs) |

## Badge System

Color-coded badges for categories, alert types, and severity levels:
- **b-green** — growth, momentum, emerging
- **b-red** — critical severity, declining, security category
- **b-amber** — bubble warning, high severity, frontend/emerging category
- **b-blue** — AI/ML category, analytics
- **b-teal** — emerging skill, cloud category
- **b-indigo** — disruption, DevOps/backend category
- **b-gray** — default, low severity
