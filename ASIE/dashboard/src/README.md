# `dashboard/src/` — React Source Code

> All frontend components, API client, and styles for the ASIE dashboard.

## Files

| File | Purpose | Exports |
|---|---|---|
| `main.jsx` | React DOM entry point — mounts `<App />` into `#root` | — |
| `App.jsx` | Full application: global styles, all components, 5 tab views, main `App` component | `default: App` |
| `api.js` | API client wrapping `fetch()` for all backend endpoints | `api` object |
| `index.css` | Global CSS imports (Tailwind base/components/utilities) | — |

## Component Architecture (`App.jsx`)

The entire UI is built as a single-file React application (~1100 lines) with the following component hierarchy:

```
App
├── StyleTag                    # Injects global CSS variables + animations
├── Header
│   ├── Clock                   # Live date/time (updates every second)
│   ├── Brand (ASIE logo)
│   ├── NavBar (5 tabs)
│   └── Live Data indicator
├── Main
│   ├── OverviewTab
│   │   ├── KpiStrip (4 KPI cards)
│   │   ├── EditorialRow
│   │   │   ├── Panel → BarChart (Top Growing)
│   │   │   └── Panel → BarChart (Highest Risk)
│   │   └── EditorialRow
│   │       ├── Panel → AlertItem list
│   │       └── Panel → RankRow lists (Trending + Emerging)
│   ├── ForecastTab
│   │   ├── Skill Selector (dropdown)
│   │   ├── KPI Grid (6 metrics)
│   │   ├── EditorialRow
│   │   │   ├── Panel → AreaChart + LineChart (5-Year Forecast)
│   │   │   └── Panel → RadarChart (Skill Health)
│   │   └── Panel → ScoreBar list (SHAP Feature Impact)
│   ├── SkillsTableTab
│   │   ├── Search Input
│   │   └── Sortable Table (8 columns)
│   ├── ResumeTab
│   │   ├── Textarea + Industry/Role selectors
│   │   ├── KpiStrip (4 result KPIs)
│   │   ├── EditorialRow
│   │   │   ├── Panel → SkillGap list
│   │   │   └── Panel → RoleFit list or IndustryFit BarChart
│   │   └── Panel → Recommended Skills badges
│   └── AlertsTab
│       └── EditorialRow
│           ├── Panel → AlertItem list
│           └── Panels → PieChart + BarChart
└── Footer
```

## Reusable Components

| Component | Props | Description |
|---|---|---|
| `Panel` | `children`, `style` | White content panel container |
| `PanelLabel` | `children` | Mono uppercase label with green dash prefix |
| `PanelTitle` | `children`, `style` | Bold section title |
| `EditorialRow` | `children`, `cols`, `style` | CSS grid row with bordered panels |
| `SectionHeader` | `num`, `title`, `sub` | Section header with number/title/subtitle |
| `KpiStrip` | `cells[]` | Horizontal KPI card grid with accent bars |
| `ScoreBar` | `label`, `value`, `color` | Horizontal progress bar (0–100%) |
| `RankRow` | `rank`, `name`, `value`, `valueColor` | Numbered list row |
| `AlertItem` | `alert` | Alert card with type/severity badges |
| `Badge` | `variant`, `children`, `style` | Color-coded tag badge |

## Styling Approach

- **CSS-in-JS** — inline styles for all components (no external CSS modules)
- **CSS Variables** — defined in `:root` via `StyleTag` component
- **Animations** — `reveal` (fade-in slide), `blink` (live indicator), `countUp`
- **Typography** — 3 font families loaded from Google Fonts
- **Recharts customization** — shared axis styles (`AX`), grid color, tooltip styling

## Data Flow

```
Backend API (port 8000)
        │
        ▼
  api.js (fetch wrapper)
        │
        ▼
  App component (useEffect on mount)
        │
  Promise.all([getSummary, getSkills, getTrending, getEmerging, getAlerts])
        │
        ▼
  React State (summary, skills, trending, emerging, alerts)
        │
        ▼
  Tab Components render from state
```

Each tab renders conditionally based on `tab` state. Forecast tab makes an additional API call when a skill is selected.

## API Client (`api.js`)

Simple fetch wrapper — all endpoints go through `/api/v1` prefix (proxied by Vite in dev):

```javascript
const BASE = '/api/v1';

async function fetchJSON(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
```

17 endpoint functions: `getSkills`, `getSkillForecast`, `getTrending`, `getEmerging`, `getAtRisk`, `getAlerts`, `getSummary`, `getGraph`, `getNeighbors`, `getLearningPath`, `filterByGeo`, `filterByIndustry`, `getRoles`, `analyzeResume`.
