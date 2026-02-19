import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, AreaChart, Area, Cell,
  PieChart, Pie, Legend, ComposedChart,
} from 'recharts';
import { api } from './api';

/* ─── Google Fonts injection ─────────────────────────────── */
const fontLink = document.createElement('link');
fontLink.rel = 'stylesheet';
fontLink.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap';
document.head.appendChild(fontLink);

/* ─── Global styles ──────────────────────────────────────── */
const globalStyles = `
  *, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }
  :root {
    --ink:     #000000;
    --paper:   #ffffff;
    --paper2:  #f8fafc;
    --paper3:  #e2e8f0;
    --rule:    #e2e8f0;
    --rule2:   rgba(0,0,0,0.06);
    --accent:  #2563eb;
    --gold:    #d97706;
    --teal:    #0d9488;
    --indigo:  #4f46e5;
    --red:     #dc2626;
    --text-h:  #0f172a;
    --text-b:  #334155;
    --text-m:  #64748b;
    --text-l:  #94a3b8;
    --font-d:  'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-b:  'Inter', sans-serif;
    --font-m:  'JetBrains Mono', 'Cascadia Code', 'Fira Code', monospace;
    --r:  10px;
    --r2: 6px;
  }
  html { scroll-behavior: smooth; }
  body {
    background: #f8fafc;
    color: var(--text-b);
    font-family: var(--font-d);
    font-size: 15px;
    line-height: 1.6;
    min-height: 100vh;
    overflow-x: hidden;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.2} }
  @keyframes reveal {
    from { opacity:0; transform:translateY(14px); }
    to   { opacity:1; transform:translateY(0); }
  }
  @keyframes countUp {
    from { opacity:0; }
    to   { opacity:1; }
  }
  .tab-panel { animation: reveal .35s cubic-bezier(.16,1,.3,1) both; }
  .dot-live {
    width:7px; height:7px; border-radius:50%;
    background:#22c55e;
    box-shadow: 0 0 8px rgba(34,197,94,0.5);
    animation: blink 2s ease-in-out infinite;
    display:inline-block; flex-shrink:0;
  }
  /* scrollbars */
  ::-webkit-scrollbar { width:6px; height:6px; }
  ::-webkit-scrollbar-track { background: #f1f5f9; }
  ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius:3px; }
  /* panel-label pseudo line */
  .panel-label-line::before {
    content:'';
    display:inline-block;
    width:16px; height:2px;
    background:#2563eb;
    margin-right:8px;
    vertical-align:middle;
    border-radius:1px;
  }
  /* score bar transition */
  .sbar-fill { transition: width .7s cubic-bezier(.4,0,.2,1); }
  /* kpi cell hover */
  .kpi-cell:hover { background: #f1f5f9 !important; }
  /* table row hover */
  .tbl-row:hover { background: #f1f5f9 !important; }
  /* nav button */
  .nav-btn { border-bottom: 2px solid transparent; transition: color .2s, border-color .2s; }
  .nav-btn:hover { color: #0f172a; }
  .nav-btn.active { color:#0f172a; border-bottom-color:#2563eb; font-weight:700; }
  /* primary button */
  .btn-primary { transition: all .18s; }
  .btn-primary:hover:not(:disabled) { background: #1d4ed8 !important; box-shadow: 0 4px 16px rgba(37, 100, 235, 0.68); }
  .btn-primary:disabled { opacity:.5; cursor:not-allowed; }
  /* input focus */
  .asie-input:focus { border-color: #2563eb !important; box-shadow: 0 0 0 3px rgba(37,99,235,.1) !important; outline:none; }
  .asie-select:focus { border-color: #2563eb !important; box-shadow: 0 0 0 3px rgba(37,99,235,.1) !important; outline:none; }
`;

const StyleTag = () => <style dangerouslySetInnerHTML={{ __html: globalStyles }} />;

/* ─── Utility helpers ────────────────────────────────────── */
const pct = v => `${(v * 100).toFixed(1)}%`;
const fmt = v => typeof v === 'number' ? v.toFixed(2) : v;

const growthC = v => v > .65 ? '#16a34a' : v > .4 ? '#0d9488' : '#dc2626';
const riskC = v => v > .6 ? '#dc2626' : v > .35 ? '#ca8a04' : '#16a34a';

/* ─── Badge system ───────────────────────────────────────── */
const BADGE_STYLES = {
  'b-red': { background: '#fef2f2', color: '#dc2626', border: '1px solid #fecaca' },
  'b-amber': { background: '#fefce8', color: '#ca8a04', border: '1px solid #fde68a' },
  'b-blue': { background: '#eff6ff', color: '#2563eb', border: '1px solid #bfdbfe' },
  'b-green': { background: '#f0fdf4', color: '#16a34a', border: '1px solid #bbf7d0' },
  'b-teal': { background: '#f0fdfa', color: '#0d9488', border: '1px solid #99f6e4' },
  'b-indigo': { background: '#eef2ff', color: '#4338ca', border: '1px solid #c7d2fe' },
  'b-gray': { background: '#f9fafb', color: '#6b7280', border: '1px solid #e5e7eb' },
};

const ALERT_TYPE_BADGE = {
  momentum_spike: 'b-green', bubble_warning: 'b-amber',
  emerging_skill: 'b-teal', declining_skill: 'b-red', disruption: 'b-indigo',
};
const SEV_BADGE = { critical: 'b-red', high: 'b-amber', medium: 'b-teal', low: 'b-gray' };

const CAT_BADGE = {
  'AI/ML': 'b-blue', 'Cloud': 'b-teal', 'DevOps': 'b-indigo', 'Security': 'b-red',
  'Data': 'b-green', 'Frontend': 'b-amber', 'Systems': 'b-gray', 'Emerging': 'b-amber',
  'Analytics': 'b-blue', 'QA': 'b-red', 'Backend': 'b-indigo', 'Languages': 'b-green',
};

function Badge({ variant = 'b-gray', children, style: extraStyle = {} }) {
  const s = BADGE_STYLES[variant] || BADGE_STYLES['b-gray'];
  return (
    <span style={{
      fontFamily: 'var(--font-m)', fontSize: 11, fontWeight: 500,
      letterSpacing: '.04em', textTransform: 'uppercase',
      padding: '4px 10px', borderRadius: 4, display: 'inline-block',
      whiteSpace: 'nowrap',
      ...s, ...extraStyle,
    }}>
      {children}
    </span>
  );
}

/* ─── Chart tooltip style ────────────────────────────────── */
const TOOLTIP_STYLE = {
  contentStyle: {
    background: '#ffffff', border: '1px solid #e2e8f0',
    borderRadius: 8, padding: 12,
    fontFamily: 'var(--font-m)', fontSize: 13, color: '#334155',
    boxShadow: '0 4px 12px rgb(0, 0, 0)',
  },
  labelStyle: { color: '#000000', fontWeight: 600 },
};

/* ─── Panel wrapper ──────────────────────────────────────── */
function Panel({ children, style = {} }) {
  return (
    <div style={{
      padding: 24, background: 'var(--paper)',
      position: 'relative', zIndex: 1, ...style,
    }}>
      {children}
    </div>
  );
}

function PanelLabel({ children }) {
  return (
    <div className="panel-label-line" style={{
      fontFamily: 'var(--font-m)', fontSize: 11, letterSpacing: '.08em',
      textTransform: 'uppercase', color: 'var(--text-m)',
      marginBottom: 14, display: 'flex', alignItems: 'center',
    }}>
      {children}
    </div>
  );
}

function PanelTitle({ children, style = {} }) {
  return (
    <div style={{
      fontSize: 20, fontWeight: 700, color: 'var(--text-h)',
      letterSpacing: '-.02em', marginBottom: 16, lineHeight: 1.3, ...style,
    }}>
      {children}
    </div>
  );
}

/* ─── Editorial row ──────────────────────────────────────── */
function EditorialRow({ children, cols = '1fr 1fr', style = {} }) {
  return (
    <div style={{
      display: 'grid', gridTemplateColumns: cols,
      border: '1px solid var(--rule)', borderRadius: 'var(--r)',
      overflow: 'hidden', marginBottom: 20, ...style,
    }}>
      {React.Children.map(children, (child, i) =>
        child ? React.cloneElement(child, {
          style: {
            borderRight: i < React.Children.count(children) - 1 ? '1px solid var(--rule)' : 'none',
            ...(child.props.style || {}),
          }
        }) : null
      )}
    </div>
  );
}

/* ─── Section Header ─────────────────────────────────────── */
function SectionHeader({ num, title, sub }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'baseline', gap: 14,
      padding: '28px 0 18px',
      borderBottom: '2px solid var(--rule)', marginBottom: 24,
    }}>
      <span style={{ fontFamily: 'var(--font-m)', fontSize: 13, color: '#2563eb', letterSpacing: '.06em', fontWeight: 600 }}>{num}</span>
      <span style={{ fontSize: 26, fontWeight: 800, color: 'var(--text-h)', letterSpacing: '-.02em', lineHeight: 1 }}>{title}</span>
      <span style={{ fontFamily: 'var(--font-b)', fontSize: 14, color: 'var(--text-m)', marginLeft: 'auto', fontWeight: 500 }}>{sub}</span>
    </div>
  );
}

/* ─── KPI Strip ──────────────────────────────────────────── */
function KpiStrip({ cells }) {
  return (
    <div style={{
      display: 'grid', gridTemplateColumns: `repeat(${cells.length},1fr)`,
      border: '1px solid var(--rule)', borderRadius: 'var(--r)',
      overflow: 'hidden', marginBottom: 24,
    }}>
      {cells.map((c, i) => (
        <div key={i} className="kpi-cell" style={{
          padding: '22px 24px',
          borderRight: i < cells.length - 1 ? '1px solid var(--rule)' : 'none',
          position: 'relative', background: 'var(--paper)', cursor: 'default',
          transition: 'background .2s',
        }}>
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, background: c.accent, borderRadius: '0 0 2px 2px' }} />
          <div style={{ fontFamily: 'var(--font-m)', fontSize: 12, letterSpacing: '.06em', textTransform: 'uppercase', color: 'var(--text-m)', marginBottom: 10, fontWeight: 500 }}>{c.label}</div>
          <div style={{ fontSize: 38, fontWeight: 800, letterSpacing: '-.03em', lineHeight: 1, color: c.valColor || 'var(--text-h)', fontFamily: 'var(--font-d)' }}>
            {c.value}
          </div>
          <div style={{ fontFamily: 'var(--font-m)', fontSize: 12, marginTop: 8, color: c.deltaColor || 'var(--text-m)', display: 'flex', alignItems: 'center', gap: 4 }}>{c.delta}</div>
        </div>
      ))}
    </div>
  );
}

/* ─── Score Bar ──────────────────────────────────────────── */
function ScoreBar({ label, value, color = 'linear-gradient(90deg,#2563eb,#0d9488)' }) {
  const pctVal = Math.min(value * 100, 100).toFixed(0);
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
      <span style={{ width: 140, fontSize: 14, color: 'var(--text-m)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', flexShrink: 0, fontWeight: 500 }}>{label}</span>
      <div style={{ flex: 1, height: 6, background: '#e2e8f0', borderRadius: 3, overflow: 'hidden' }}>
        <div className="sbar-fill" style={{ height: '100%', borderRadius: 3, width: `${pctVal}%`, background: color }} />
      </div>
      <span style={{ width: 42, textAlign: 'right', fontFamily: 'var(--font-m)', fontSize: 13, color: 'var(--text-m)', fontWeight: 500 }}>{pctVal}%</span>
    </div>
  );
}

/* ─── Rank Row ───────────────────────────────────────────── */
function RankRow({ rank, name, value, valueColor = '#2563eb' }) {
  return (
    <div style={{
      display: 'grid', gridTemplateColumns: '30px 1fr auto',
      alignItems: 'center', gap: 12, padding: '10px 0',
      borderBottom: '1px solid var(--rule2)', fontSize: 15,
    }}>
      <span style={{ fontFamily: 'var(--font-m)', fontSize: 13, color: 'var(--text-l)', textAlign: 'center', padding: '2px 0', fontWeight: 500 }}>{rank}</span>
      <span style={{ color: 'var(--text-b)', fontWeight: 600 }}>{name}</span>
      <span style={{ fontFamily: 'var(--font-m)', fontSize: 14, fontWeight: 600, color: valueColor }}>{value}</span>
    </div>
  );
}

/* ─── Alert Item ─────────────────────────────────────────── */
function AlertItem({ alert }) {
  const typeKey = alert.alert_type || alert.type || '';
  const sevKey = alert.severity || alert.sev || '';
  const skillName = alert.skill_name || alert.skill || '';
  const msg = alert.message || alert.msg || '';

  return (
    <div style={{ padding: '14px 0', borderBottom: '1px solid var(--rule2)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 6 }}>
        <Badge variant={ALERT_TYPE_BADGE[typeKey] || 'b-gray'}>{typeKey.replace(/_/g, ' ')}</Badge>
        <Badge variant={SEV_BADGE[sevKey] || 'b-gray'}>{sevKey}</Badge>
        <span style={{ marginLeft: 'auto', fontFamily: 'var(--font-m)', fontSize: 13, color: 'var(--text-l)', fontWeight: 500 }}>{skillName}</span>
      </div>
      <div style={{ fontSize: 15, color: 'var(--text-m)', lineHeight: 1.6 }}>{msg}</div>
    </div>
  );
}

/* ─── Recharts shared axis styles ────────────────────────── */
const AX = { tick: { fill: '#64748b', fontSize: 12, fontFamily: 'var(--font-m)' }, axisLine: false, tickLine: false };
const GRID_COLOR = 'rgba(0,0,0,0.06)';

/* ─── Ghost Bar colors ───────────────────────────────────── */
const GHOST_FILLS = ['rgba(37,99,235,0.08)', 'rgba(13,148,136,0.08)', 'rgba(79,70,229,0.08)', 'rgba(22,163,74,0.08)', 'rgba(217,119,6,0.08)', 'rgba(13,148,136,0.08)'];
const GHOST_STROKES = ['#2563eb', '#0d9488', '#4f46e5', '#16a34a', '#d97706', '#0f766e'];

/* ══════════════════════════════════════════════════════════
   TAB: Overview
══════════════════════════════════════════════════════════ */
function OverviewTab({ summary, trending, emerging, alerts }) {
  if (!summary) return <p style={{ color: 'var(--text-m)', padding: 40, textAlign: 'center', fontSize: 16 }}>Loading…</p>;

  const topGrowing = summary.top_growing || [];
  const highestRisk = summary.highest_risk || [];

  return (
    <div className="tab-panel">
      <SectionHeader num="01 /" title="Market Intelligence Overview" sub="Real-time skill demand signals" />

      <KpiStrip cells={[
        { label: 'Skills Tracked', value: summary.total_skills_tracked, accent: '#16a34a', delta: '↗ 6 new this month', deltaColor: '#2563eb' },
        { label: 'Avg Growth Score', value: pct(summary.avg_growth_score), accent: '#0d9488', delta: '↑ 4.2% vs last month', deltaColor: '#0d9488' },
        { label: 'Avg Auto Risk', value: pct(summary.avg_automation_risk), accent: '#ca8a04', delta: 'Moderate exposure', deltaColor: '#ca8a04' },
        { label: 'Active Alerts', value: summary.active_alerts, accent: '#dc2626', delta: '3 critical · 5 high', deltaColor: '#16a34a' },
      ]} />

      {/* Top Growing + Highest Risk */}
      <EditorialRow cols="1fr 1fr">
        <Panel>
          <PanelLabel>Growth Ranking</PanelLabel>
          <PanelTitle>Top Growing Skills</PanelTitle>
          <div style={{ height: 210 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topGrowing} layout="vertical" margin={{ left: 0, right: 8, top: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} horizontal={false} />
                <XAxis type="number" domain={[0, 1]} {...AX} tickFormatter={v => (v * 100) + '%'}
                  label={{ value: 'Growth Score (0–100%)', position: 'insideBottom', offset: -14, fill: '#64748b', fontSize: 11, fontFamily: 'var(--font-m)' }} />
                <YAxis type="category" dataKey="name" {...AX} width={130}
                  label={{ value: '', angle: -90 }} />
                <Tooltip {...TOOLTIP_STYLE} formatter={v => [(v * 100).toFixed(1) + '%', 'Growth']} />
                <Bar dataKey="growth" radius={4} isAnimationActive>
                  {topGrowing.map((_, i) => (
                    <Cell key={i} fill={GHOST_FILLS[i % GHOST_FILLS.length]} stroke={GHOST_STROKES[i % GHOST_STROKES.length]} strokeWidth={1.5} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel>
          <PanelLabel>Automation Exposure</PanelLabel>
          <PanelTitle>Highest Risk Skills</PanelTitle>
          <div style={{ height: 210 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={highestRisk} layout="vertical" margin={{ left: 0, right: 8, top: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} horizontal={false} />
                <XAxis type="number" domain={[0, 1]} {...AX} tickFormatter={v => (v * 100) + '%'}
                  label={{ value: 'Automation Risk Score (0–100%)', position: 'insideBottom', offset: -14, fill: '#64748b', fontSize: 11, fontFamily: 'var(--font-m)' }} />
                <YAxis type="category" dataKey="name" {...AX} width={130} />
                <Tooltip {...TOOLTIP_STYLE} formatter={v => [(v * 100).toFixed(1) + '%', 'Risk']} />
                <Bar dataKey="risk" radius={4} isAnimationActive>
                  {highestRisk.map((s, i) => {
                    const v = s.risk ?? s.automation_risk ?? 0;
                    const fill = v > .6 ? 'rgba(220,38,38,0.10)' : v > .35 ? 'rgba(202,138,4,0.10)' : 'rgba(22,163,74,0.12)';
                    const stroke = v > .6 ? '#dc2626' : v > .35 ? '#ca8a04' : '#16a34a';
                    return <Cell key={i} fill={fill} stroke={stroke} strokeWidth={1.5} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </EditorialRow>

      {/* Alert Feed + Trending + Emerging */}
      <EditorialRow cols="2fr 1fr">
        <Panel>
          <PanelLabel>Alert Feed</PanelLabel>
          <PanelTitle>Recent Signals</PanelTitle>
          <div style={{ maxHeight: 260, overflowY: 'auto' }}>
            {(alerts || []).slice(0, 6).map((a, i) => <AlertItem key={i} alert={a} />)}
          </div>
        </Panel>

        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <Panel style={{ flex: 1, borderBottom: '1px solid var(--rule)' }}>
            <PanelLabel>By Momentum Index</PanelLabel>
            <PanelTitle style={{ fontSize: 17, marginBottom: 12 }}>Trending</PanelTitle>
            <div style={{ maxHeight: 130, overflowY: 'auto' }}>
              {(trending || []).slice(0, 6).map((s, i) => (
                <RankRow key={i} rank={i + 1} name={s.name} value={(s.momentum_index ?? s.momentum ?? 0).toFixed(2)} valueColor="#16a34a" />
              ))}
            </div>
          </Panel>
          <Panel style={{ flex: 1 }}>
            <PanelLabel>Emergence Score</PanelLabel>
            <PanelTitle style={{ fontSize: 17, marginBottom: 12 }}>Emerging</PanelTitle>
            <div style={{ maxHeight: 130, overflowY: 'auto' }}>
              {(emerging || []).slice(0, 6).map((s, i) => (
                <RankRow key={i} rank={i + 1} name={s.name} value={(s.emergence_score ?? 0).toFixed(2)} valueColor="#0d9488" />
              ))}
            </div>
          </Panel>
        </div>
      </EditorialRow>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════
   TAB: Forecast
══════════════════════════════════════════════════════════ */
function ForecastTab({ skills }) {
  const [selected, setSelected] = useState('');
  const [forecast, setForecast] = useState(null);

  useEffect(() => {
    if (selected) {
      api.getSkillForecast(selected).then(setForecast).catch(console.error);
    } else {
      setForecast(null);
    }
  }, [selected]);

  const fc = forecast?.forecast;
  const explanations = forecast?.explanations;

  const chartData = (fc?.predicted_demand || []).map((v, i) => ({
    month: `M${i + 1}`,
    demand: parseFloat(v.toFixed(4)),
    lower: fc?.prediction_intervals?.[i]?.lower,
    upper: fc?.prediction_intervals?.[i]?.upper,
  }));

  const radarData = fc ? [
    { metric: 'Growth', value: fc.growth_score },
    { metric: 'Confidence', value: fc.confidence_score },
    { metric: 'Reliability', value: fc.reliability_score || 0.5 },
    { metric: 'Low Volatility', value: 1 - fc.volatility_score },
    { metric: 'Low Risk', value: 1 - fc.automation_risk },
    { metric: 'No Bubble', value: 1 - fc.bubble_score },
  ] : [];

  const fcKpis = fc ? [
    { label: 'Growth', value: pct(fc.growth_score), accent: growthC(fc.growth_score), valColor: growthC(fc.growth_score) },
    { label: 'Confidence', value: pct(fc.confidence_score), accent: '#0d9488', valColor: '#0d9488' },
    { label: 'Volatility', value: pct(fc.volatility_score), accent: '#ca8a04', valColor: '#ca8a04' },
    { label: 'Momentum', value: fmt(fc.momentum_index), accent: '#16a34a', valColor: '#16a34a' },
    { label: 'Bubble', value: pct(fc.bubble_score), accent: '#ca8a04', valColor: '#ca8a04' },
    { label: 'Auto Risk', value: pct(fc.automation_risk), accent: riskC(fc.automation_risk), valColor: riskC(fc.automation_risk) },
  ] : [];

  const skillName = (skills || []).find(s => s.skill_id === selected)?.name || '';
  const narrative = fc
    ? `${skillName} shows ${fc.growth_score > .75 ? 'strong' : 'moderate'} long-term demand with a momentum index of ${fmt(fc.momentum_index)}. Key drivers include industry adoption, job posting velocity, and university curriculum integration. ${fc.bubble_score > .3 ? '⚠️ Rising bubble score warrants caution.' : 'Fundamentals remain solid — no saturation signals detected.'}`
    : '';

  return (
    <div className="tab-panel">
      <SectionHeader num="02 /" title="Demand Forecast Engine" sub="5-year predictive analysis" />

      {/* Skill Selector */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontFamily: 'var(--font-m)', fontSize: 12, letterSpacing: '.06em', textTransform: 'uppercase', color: 'var(--text-m)', marginBottom: 8, display: 'flex', alignItems: 'center' }}>
          <span className="panel-label-line">Select Skill</span>
        </div>
        <select
          className="asie-select"
          value={selected}
          onChange={e => setSelected(e.target.value)}
          style={{
            width: '100%', padding: '12px 16px',
            background: 'var(--paper2)', border: '1px solid var(--rule)', borderRadius: 'var(--r2)',
            color: 'var(--text-b)', fontFamily: 'var(--font-d)', fontSize: 15, fontWeight: 600,
            cursor: 'pointer', transition: 'border-color .18s',
          }}
        >
          <option value="">— Select a skill to generate forecast —</option>
          {(skills || []).map(s => (
            <option key={s.skill_id} value={s.skill_id}>{s.name}</option>
          ))}
        </select>
      </div>

      {!fc && (
        <div style={{ padding: 48, textAlign: 'center', border: '1px dashed var(--rule)', borderRadius: 'var(--r)', color: 'var(--text-l)' }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>📊</div>
          <div style={{ fontSize: 16 }}>Select a skill above to generate its demand forecast and health analysis.</div>
        </div>
      )}

      {fc && (
        <>
          {/* FC KPIs */}
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(6,1fr)',
            border: '1px solid var(--rule)', borderRadius: 'var(--r)',
            overflow: 'hidden', marginBottom: 20,
          }}>
            {fcKpis.map((k, i) => (
              <div key={i} style={{
                padding: '18px 16px', textAlign: 'center',
                borderRight: i < 5 ? '1px solid var(--rule)' : 'none',
                background: 'var(--paper2)',
              }}>
                <div style={{ fontFamily: 'var(--font-m)', fontSize: 11, letterSpacing: '.06em', textTransform: 'uppercase', color: 'var(--text-l)', marginBottom: 8, fontWeight: 500 }}>{k.label}</div>
                <div style={{ fontSize: 24, fontWeight: 800, letterSpacing: '-.02em', color: k.valColor || 'var(--text-h)' }}>{k.value}</div>
              </div>
            ))}
          </div>

          {/* Line + Radar */}
          <EditorialRow cols="2fr 1fr" style={{ marginBottom: 20 }}>
            <Panel>
              <PanelLabel>Predictive Demand Curve</PanelLabel>
              <PanelTitle>5-Year Forecast</PanelTitle>
              <div style={{ height: 260 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={chartData} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
                    <defs>
                      <linearGradient id="fcBand" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#1e40af" stopOpacity={0.45} />
                        <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.10} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke={GRID_COLOR} strokeDasharray="3 3" />
                    <XAxis dataKey="month" {...AX} interval={9} />
                    <YAxis {...AX} />
                    <Tooltip {...TOOLTIP_STYLE} formatter={v => [parseFloat(v).toFixed(3), 'Demand']} />
                    <Area type="monotone" dataKey="upper" stroke="rgba(30,64,175,0.25)" strokeWidth={1} fill="url(#fcBand)" />
                    <Area type="monotone" dataKey="lower" stroke="rgba(30,64,175,0.25)" strokeWidth={1} fill="#ffffff" />
                    <Line type="monotone" dataKey="demand" stroke="#1e3a8a" strokeWidth={3} dot={false} activeDot={{ r: 5, fill: '#1e3a8a', stroke: '#fff', strokeWidth: 2 }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </Panel>

            <Panel>
              <PanelLabel>Multi-Axis Health</PanelLabel>
              <PanelTitle>Skill Radar</PanelTitle>
              <div style={{ height: 250 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={radarData}>
                    <PolarGrid stroke={GRID_COLOR} />
                    <PolarAngleAxis dataKey="metric" tick={{ fill: '#64748b', fontSize: 12, fontFamily: 'var(--font-m)' }} />
                    <PolarRadiusAxis domain={[0, 1]} tick={false} axisLine={false} />
                    <Radar dataKey="value" stroke="#16a34a" fill="#16a34a" fillOpacity={0.10} strokeWidth={2}
                      dot={{ fill: '#16a34a', r: 3 }} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </Panel>
          </EditorialRow>

          {/* SHAP */}
          {explanations && (
            <div style={{ border: '1px solid var(--rule)', borderRadius: 'var(--r)', overflow: 'hidden', marginBottom: 20 }}>
              <Panel style={{ borderRight: 'none' }}>
                <PanelLabel>Explainability Layer</PanelLabel>
                <PanelTitle>SHAP Feature Impact</PanelTitle>
                <p style={{
                  fontSize: 15, color: 'var(--text-m)', lineHeight: 1.7,
                  marginBottom: 20, padding: '16px 18px',
                  background: '#f1f5f9',
                  borderLeft: '3px solid #2563eb',
                  borderRadius: '0 var(--r2) var(--r2) 0',
                }}>
                  {narrative}
                </p>
                <div>
                  {Object.entries(explanations.feature_impacts || {}).slice(0, 8).map(([feat, impact]) => (
                    <ScoreBar key={feat} label={feat} value={impact} />
                  ))}
                </div>
              </Panel>
            </div>
          )}
        </>
      )}
    </div>
  );
}

/* ══════════════════════════════════════════════════════════
   TAB: Skills Table
══════════════════════════════════════════════════════════ */
function SkillsTableTab({ skills }) {
  const [sortCol, setSortCol] = useState('growth_score');
  const [sortDir, setSortDir] = useState(-1);
  const [query, setQuery] = useState('');

  const toggleSort = col => {
    if (sortCol === col) setSortDir(d => d * -1);
    else { setSortCol(col); setSortDir(-1); }
  };

  const rows = (skills || [])
    .filter(s => s.name.toLowerCase().includes(query.toLowerCase()) || (s.category || '').toLowerCase().includes(query.toLowerCase()))
    .sort((a, b) => typeof a[sortCol] === 'string' ? a[sortCol].localeCompare(b[sortCol]) * sortDir : (a[sortCol] - b[sortCol]) * sortDir);

  const Th = ({ label, col }) => (
    <th onClick={() => toggleSort(col)} style={{
      padding: '13px 16px', fontFamily: 'var(--font-m)', fontSize: 11,
      fontWeight: 600, letterSpacing: '.06em', textTransform: 'uppercase',
      color: sortCol === col ? '#0f172a' : '#64748b',
      textAlign: 'left', cursor: 'pointer', userSelect: 'none', whiteSpace: 'nowrap',
      borderRight: '1px solid #e2e8f0', borderBottom: '2px solid #e2e8f0',
    }}>
      {label} {sortCol === col ? (sortDir > 0 ? '↑' : '↓') : '↕'}
    </th>
  );

  return (
    <div className="tab-panel">
      <SectionHeader num="03 /" title="Skill Intelligence Registry" sub={`${rows.length} skill${rows.length !== 1 ? 's' : ''} tracked`} />

      <div style={{ marginBottom: 14, display: 'flex', justifyContent: 'flex-end' }}>
        <input
          className="asie-input"
          type="search"
          placeholder="Search skills…"
          value={query}
          onChange={e => setQuery(e.target.value)}
          style={{
            width: 260, background: 'var(--paper2)', border: '1px solid var(--rule)',
            borderRadius: 'var(--r2)', padding: '10px 14px',
            color: 'var(--text-b)', fontFamily: 'var(--font-d)', fontSize: 15,
            transition: 'border-color .18s, box-shadow .18s',
          }}
        />
      </div>

      <div style={{ border: '1px solid var(--rule)', borderRadius: 'var(--r)', overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead style={{ background: '#f8fafc', position: 'sticky', top: 0, zIndex: 2 }}>
              <tr>
                <th style={{ padding: '13px 16px', fontFamily: 'var(--font-m)', fontSize: 11, fontWeight: 600, letterSpacing: '.06em', textTransform: 'uppercase', color: '#64748b', textAlign: 'left', borderRight: '1px solid #e2e8f0', borderBottom: '2px solid #e2e8f0' }}>
                  Skill Name
                </th>
                <Th label="Category" col="category" />
                <Th label="Growth" col="growth_score" />
                <Th label="Confidence" col="confidence_score" />
                <Th label="Volatility" col="volatility_score" />
                <Th label="Momentum" col="momentum_index" />
                <Th label="Bubble" col="bubble_score" />
                <th style={{ padding: '13px 16px', fontFamily: 'var(--font-m)', fontSize: 11, fontWeight: 600, letterSpacing: '.06em', textTransform: 'uppercase', color: '#64748b', textAlign: 'left', cursor: 'pointer', borderBottom: '2px solid #e2e8f0' }} onClick={() => toggleSort('automation_risk')}>
                  Auto Risk {sortCol === 'automation_risk' ? (sortDir > 0 ? '↑' : '↓') : '↕'}
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map(s => (
                <tr key={s.skill_id} className="tbl-row" style={{ borderBottom: '1px solid var(--rule2)', transition: 'background .12s' }}>
                  <td style={{ padding: '12px 16px', fontWeight: 700, fontSize: 15 }}>{s.name}</td>
                  <td style={{ padding: '12px 16px' }}>
                    <Badge variant={CAT_BADGE[s.category] || 'b-gray'}>{s.category}</Badge>
                  </td>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-m)', fontSize: 14, color: growthC(s.growth_score), fontWeight: 600 }}>{pct(s.growth_score)}</td>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-m)', fontSize: 14 }}>{pct(s.confidence_score)}</td>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-m)', fontSize: 14, color: '#d97706' }}>{pct(s.volatility_score)}</td>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-m)', fontSize: 14, color: '#16a34a', fontWeight: 600 }}>{fmt(s.momentum_index)}</td>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-m)', fontSize: 14 }}>{pct(s.bubble_score)}</td>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-m)', fontSize: 14, color: riskC(s.automation_risk), fontWeight: 600 }}>{pct(s.automation_risk)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════
   TAB: Resume
══════════════════════════════════════════════════════════ */
function ResumeTab() {
  const [text, setText] = useState('');
  const [industry, setIndustry] = useState('');
  const [role, setRole] = useState('');
  const [roles, setRoles] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [inputMode, setInputMode] = useState('paste'); // 'paste' | 'upload'

  useEffect(() => {
    setRole('');
    api.getRoles(industry).then(r => setRoles(r.roles || [])).catch(() => setRoles([]));
  }, [industry]);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const validExts = ['pdf', 'docx', 'txt'];
    const ext = file.name.split('.').pop().toLowerCase();
    if (!validExts.includes(ext)) {
      alert('Please upload a PDF, DOCX, or TXT file.');
      e.target.value = '';
      return;
    }
    setUploadedFile(file);
  };

  const analyze = async () => {
    if (inputMode === 'paste' && !text.trim()) { alert('Please paste your resume text first.'); return; }
    if (inputMode === 'upload' && !uploadedFile) { alert('Please select a file to upload.'); return; }
    if (!role) { alert('Please select a Target Role to get role-specific skill gaps.'); return; }
    setLoading(true);
    try {
      let res;
      if (inputMode === 'upload' && uploadedFile) {
        res = await api.uploadResume(uploadedFile, { target_industry: industry || null, target_role: role });
      } else {
        res = await api.analyzeResume({ resume_text: text, target_industry: industry || null, target_role: role });
      }
      setResult(res);
    } catch (e) { console.error(e); alert(e.message || 'Analysis failed'); }
    setLoading(false);
  };

  const trendIcon = o => o === 'growing' ? '🟢 Growing' : o === 'declining' ? '🔴 Declining' : '🟡 Stable';

  const resumeKpis = result ? [
    { label: 'Skills Found', value: result.extracted_skills?.length || 0, accent: '#0d9488', valColor: '#0d9488', delta: '' },
    { label: 'Readiness', value: pct(result.role_readiness_score ?? result.overall_readiness_score ?? 0), accent: '#16a34a', valColor: '#16a34a', delta: '' },
    { label: 'Gaps Found', value: result.skill_gaps?.length || 0, accent: '#ca8a04', valColor: '#ca8a04', delta: '' },
    { label: 'Recommended', value: result.top_recommended_skills?.length || 0, accent: '#16a34a', valColor: '#16a34a', delta: '' },
  ] : [];

  const gaps = result?.skill_gaps || [];
  const fitData = Object.entries(result?.industry_fit || {}).map(([k, v]) => ({ industry: k, fit: v }));
  const roleFits = result?.role_fit_results || [];

  const selectStyle = {
    background: 'var(--paper2)', border: '1px solid var(--rule)',
    borderRadius: 'var(--r2)', padding: '10px 14px',
    color: 'var(--text-b)', fontFamily: 'var(--font-d)', fontSize: 15,
    cursor: 'pointer', outline: 'none',
  };

  return (
    <div className="tab-panel">
      <SectionHeader num="04 /" title="Resume Gap Analyzer" sub="Skill readiness assessment" />

      {/* Input */}
      <div style={{ border: '1px solid var(--rule)', borderRadius: 'var(--r)', overflow: 'hidden', marginBottom: 20 }}>
        <Panel style={{ borderRight: 'none' }}>
          <PanelLabel>Input</PanelLabel>
          <PanelTitle style={{ fontSize: 18, marginBottom: 14 }}>Paste or Upload Your Resume</PanelTitle>

          {/* Mode Toggle */}
          <div style={{ display: 'flex', gap: 0, marginBottom: 14, borderRadius: 'var(--r2)', overflow: 'hidden', border: '1px solid var(--rule)', width: 'fit-content' }}>
            <button
              onClick={() => setInputMode('paste')}
              style={{
                padding: '9px 22px', border: 'none', cursor: 'pointer',
                fontFamily: 'var(--font-d)', fontSize: 14, fontWeight: 600,
                background: inputMode === 'paste' ? 'var(--ink)' : 'var(--paper2)',
                color: inputMode === 'paste' ? '#fff' : 'var(--text-m)',
                transition: 'all .18s',
              }}
            >📋 Paste Text</button>
            <button
              onClick={() => setInputMode('upload')}
              style={{
                padding: '9px 22px', border: 'none', cursor: 'pointer',
                fontFamily: 'var(--font-d)', fontSize: 14, fontWeight: 600,
                background: inputMode === 'upload' ? 'var(--ink)' : 'var(--paper2)',
                color: inputMode === 'upload' ? '#fff' : 'var(--text-m)',
                transition: 'all .18s',
              }}
            >📄 Upload File</button>
          </div>

          {inputMode === 'paste' ? (
            <textarea
              className="asie-input"
              placeholder="Paste your resume text here — PII is stripped automatically before analysis."
              value={text}
              onChange={e => setText(e.target.value)}
              style={{
                resize: 'vertical', width: '100%', minHeight: 140, lineHeight: 1.7,
                background: 'var(--paper2)', border: '1px solid var(--rule)',
                borderRadius: 'var(--r2)', padding: '12px 14px',
                color: 'var(--text-b)', fontFamily: 'var(--font-d)', fontSize: 15,
                display: 'block',
              }}
            />
          ) : (
            <div
              style={{
                width: '100%', minHeight: 130, display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center', gap: 12,
                background: 'var(--paper2)', border: '2px dashed var(--rule)',
                borderRadius: 'var(--r2)', padding: '24px 13px',
                transition: 'border-color .18s',
              }}
              onDragOver={e => { e.preventDefault(); e.currentTarget.style.borderColor = '#16a34a'; }}
              onDragLeave={e => { e.currentTarget.style.borderColor = ''; }}
              onDrop={e => {
                e.preventDefault();
                e.currentTarget.style.borderColor = '';
                const file = e.dataTransfer.files?.[0];
                if (file) {
                  const ext = file.name.split('.').pop().toLowerCase();
                  if (['pdf', 'docx', 'txt'].includes(ext)) setUploadedFile(file);
                  else alert('Please upload a PDF, DOCX, or TXT file.');
                }
              }}
            >
              <span style={{ fontSize: 32 }}>📂</span>
              <p style={{ color: 'var(--text-m)', fontSize: 15, margin: 0, textAlign: 'center' }}>
                Drag & drop your resume here, or click to browse
              </p>
              <p style={{ color: 'var(--text-m)', fontSize: 13, margin: 0, opacity: 0.7 }}>
                Supports PDF, DOCX, TXT
              </p>
              <label
                style={{
                  padding: '10px 22px', borderRadius: 'var(--r2)', cursor: 'pointer',
                  background: 'var(--ink)', color: '#fff', fontSize: 14, fontWeight: 600,
                  fontFamily: 'var(--font-d)', display: 'inline-block',
                }}
              >
                Browse Files
                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={handleFileChange}
                  style={{ display: 'none' }}
                />
              </label>
              {uploadedFile && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
                  <span style={{ fontSize: 14, color: '#16a34a', fontWeight: 600 }}>✔ {uploadedFile.name}</span>
                  <button
                    onClick={() => setUploadedFile(null)}
                    style={{
                      background: 'none', border: 'none', color: '#dc2626',
                      cursor: 'pointer', fontSize: 14, fontWeight: 700, padding: '0 4px',
                    }}
                  >✕</button>
                </div>
              )}
            </div>
          )}
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginTop: 14, flexWrap: 'wrap' }}>
            <select className="asie-select" style={selectStyle} value={industry} onChange={e => setIndustry(e.target.value)}>
              <option value="">Any Industry</option>
              {['technology', 'finance', 'healthcare', 'manufacturing', 'energy', 'education', 'retail', 'government'].map(i => (
                <option key={i} value={i}>{i.charAt(0).toUpperCase() + i.slice(1)}</option>
              ))}
            </select>
            <select className="asie-select" style={{ ...selectStyle, minWidth: 200, border: !role ? '2px solid #dc2626' : '1px solid var(--rule)' }} value={role} onChange={e => setRole(e.target.value)}>
              <option value="">— Select Target Role * —</option>
              {roles.map(r => <option key={r.role_id} value={r.role_id}>{r.display_name}</option>)}
            </select>
            <button
              className="btn-primary"
              onClick={analyze}
              disabled={loading}
              style={{
                padding: '11px 26px', borderRadius: 'var(--r2)', border: 'none',
                cursor: 'pointer', fontFamily: 'var(--font-d)', fontSize: 15, fontWeight: 700,
                letterSpacing: '.02em', background: 'var(--ink)', color: '#fff',
                display: 'inline-flex', alignItems: 'center', gap: 8,
              }}
            >
              {loading ? 'Analysing…' : 'Analyse Gaps →'}
            </button>
          </div>
          {role && roles.length > 0 && (() => {
            const r = roles.find(r => r.role_id === role);
            return r ? (
              <p style={{ fontSize: 13, color: 'var(--text-m)', marginTop: 8 }}>
                {r.description} — <strong>{trendIcon(r.trend_outlook)}</strong> (3–5 yr outlook)
              </p>
            ) : null;
          })()}
        </Panel>
      </div>

      {result && (
        <>
          {/* Clear info banner showing what was analyzed */}
          {result.target_role && (
            <div style={{
              background: 'rgba(22,163,74,0.08)', border: '1px solid rgba(22,163,74,0.25)',
              borderRadius: 'var(--r2)', padding: '12px 18px', marginBottom: 16,
              display: 'flex', alignItems: 'center', gap: 10, fontSize: 14, color: '#15803d',
              fontFamily: 'var(--font-d)', fontWeight: 600,
            }}>
              <span style={{ fontSize: 18 }}>🎯</span>
              Analysing gaps for <span style={{ textTransform: 'capitalize' }}>{result.target_role.replace(/_/g, ' ')}</span> role
              — showing only skills required for this role that are missing from your resume
            </div>
          )}

          <KpiStrip cells={resumeKpis} />

          <EditorialRow cols="1fr 1fr" style={{ marginBottom: 20 }}>
            {/* Gaps */}
            <Panel>
              <PanelLabel>Priority Order</PanelLabel>
              <PanelTitle style={{ fontSize: 18 }}>
                {result.target_role ? `Gaps for ${result.target_role.replace(/_/g, ' ')}` : 'Skill Gaps'}
              </PanelTitle>
              <div style={{ maxHeight: 300, overflowY: 'auto' }}>
                {gaps.map((g, i) => {
                  const gapScore = g.gap_score ?? 0;
                  const barColor = g.priority === 'critical' ? '#dc2626' : g.priority === 'high' ? '#d97706' : '#16a34a';
                  const badgeV = g.priority === 'critical' ? 'b-red' : g.priority === 'high' ? 'b-amber' : 'b-blue';
                  return (
                    <div key={i} style={{ padding: '12px 0', borderBottom: '1px solid var(--rule2)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                        <span style={{ fontWeight: 700, fontSize: 15 }}>{(g.skill_name || g.name || '').replace(/_/g, ' ')}</span>
                        <Badge variant={badgeV}>{g.priority}</Badge>
                      </div>
                      <ScoreBar label="Gap Score" value={gapScore} color={barColor} />
                      {g.future_trend && <p style={{ fontSize: 13, color: 'var(--text-m)', marginTop: 4 }}>{g.future_trend}</p>}
                    </div>
                  );
                })}
              </div>
            </Panel>

            {/* Role Fit or Industry Fit */}
            <Panel>
              <PanelLabel>Compatibility Score</PanelLabel>
              <PanelTitle style={{ fontSize: 18 }}>
                {result.target_role ? `Fit for ${result.target_role.replace(/_/g, ' ')}` : roleFits.length > 0 ? 'Best-Fit Roles' : 'Industry Fit'}
              </PanelTitle>
              {roleFits.length > 0 ? (
                <div style={{ maxHeight: 300, overflowY: 'auto' }}>
                  {(() => {
                    // When a role is selected, show it first prominently + top 3 alternatives
                    const targetId = result.target_role;
                    let displayRoles = roleFits;
                    if (targetId) {
                      const selected = roleFits.find(r => r.role_id === targetId);
                      const others = roleFits.filter(r => r.role_id !== targetId).slice(0, 3);
                      displayRoles = selected ? [selected, ...others] : others;
                    }
                    return displayRoles.map((rf, i) => {
                      const isTarget = targetId && rf.role_id === targetId;
                      return (
                        <div key={i} style={{ padding: '10px 0', borderBottom: '1px solid var(--rule2)', background: isTarget ? 'rgba(22,163,74,0.06)' : 'transparent', borderRadius: isTarget ? 8 : 0, paddingLeft: isTarget ? 10 : 0, paddingRight: isTarget ? 10 : 0 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                            <span style={{ fontWeight: 700, fontSize: 15 }}>{isTarget ? '★ ' : ''}{rf.role_name}</span>
                            <span style={{ fontFamily: 'var(--font-m)', fontSize: 14, fontWeight: 600, color: growthC(rf.readiness_score) }}>{pct(rf.readiness_score)}</span>
                          </div>
                          <ScoreBar label="Fit" value={rf.readiness_score} color={rf.readiness_score > .6 ? '#16a34a' : rf.readiness_score > .3 ? '#ca8a04' : '#dc2626'} />
                          {isTarget && rf.missing_required?.length > 0 && (
                            <p style={{ fontSize: 13, color: '#dc2626', marginTop: 4 }}>Missing required: {rf.missing_required.map(s => s.replace(/_/g, ' ')).join(', ')}</p>
                          )}
                          {isTarget && rf.missing_preferred?.length > 0 && (
                            <p style={{ fontSize: 13, color: '#ca8a04', marginTop: 2 }}>Nice to have: {rf.missing_preferred.map(s => s.replace(/_/g, ' ')).join(', ')}</p>
                          )}
                          {!isTarget && i > 0 && <p style={{ fontSize: 12, color: 'var(--text-m)', marginTop: 2 }}>Alternative role</p>}
                        </div>
                      );
                    });
                  })()}
                </div>
              ) : (
                <div style={{ height: 260 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={fitData} margin={{ bottom: 50 }}>
                      <CartesianGrid stroke={GRID_COLOR} strokeDasharray="3 3" />
                      <XAxis dataKey="industry" {...AX} angle={-30} textAnchor="end" height={60} />
                      <YAxis domain={[0, 1]} {...AX} tickFormatter={v => (v * 100) + '%'} />
                      <Tooltip {...TOOLTIP_STYLE} formatter={v => [(v * 100).toFixed(1) + '%', 'Fit']} />
                      <Bar dataKey="fit" radius={[4, 4, 0, 0]} isAnimationActive>
                        {fitData.map((_, i) => (
                          <Cell key={i} fill={GHOST_FILLS[i % GHOST_FILLS.length]} stroke={GHOST_STROKES[i % GHOST_STROKES.length]} strokeWidth={1.5} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </Panel>
          </EditorialRow>

          {/* Recommended Tags */}
          <div style={{ border: '1px solid var(--rule)', borderRadius: 'var(--r)', overflow: 'hidden', marginBottom: 20 }}>
            <Panel style={{ borderRight: 'none' }}>
              <PanelLabel>Learning Roadmap</PanelLabel>
              <PanelTitle style={{ fontSize: 18, marginBottom: 14 }}>
                {result.target_role ? `Learn These for ${result.target_role.replace(/_/g, ' ')}` : 'Recommended Skills'}
              </PanelTitle>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {(result.top_recommended_skills || []).slice(0, 8).map((s, i) => (
                  <Badge key={i} variant="b-teal" style={{ padding: '7px 16px', fontSize: 13 }}>{s.replace(/_/g, ' ')}</Badge>
                ))}
              </div>
            </Panel>
          </div>
        </>
      )}
    </div>
  );
}

/* ══════════════════════════════════════════════════════════
   TAB: Alerts
══════════════════════════════════════════════════════════ */
function AlertsTab({ alerts }) {
  const grouped = {};
  (alerts || []).forEach(a => {
    const k = (a.alert_type || a.type || '').replace(/_/g, ' ');
    grouped[k] = (grouped[k] || 0) + 1;
  });
  const pieData = Object.entries(grouped).map(([name, value]) => ({ name, value }));

  const sevCount = { critical: 0, high: 0, medium: 0, low: 0 };
  (alerts || []).forEach(a => { const s = a.severity || a.sev || ''; if (sevCount[s] !== undefined) sevCount[s]++; });
  const sevData = Object.entries(sevCount).map(([name, value]) => ({ name: name.charAt(0).toUpperCase() + name.slice(1), value }));

  const PIE_FILLS = ['rgba(22,163,74,0.22)', 'rgba(13,148,136,0.22)', 'rgba(37,99,235,0.22)', 'rgba(202,138,4,0.22)', 'rgba(220,38,38,0.22)'];
  const PIE_STROKES = ['#16a34a', '#0d9488', '#2563eb', '#ca8a04', '#dc2626'];
  const SEV_FILLS = ['rgba(220,38,38,0.20)', 'rgba(202,138,4,0.20)', 'rgba(22,163,74,0.20)', 'rgba(13,148,136,0.20)'];
  const SEV_STROKES = ['#dc2626', '#ca8a04', '#16a34a', '#045049'];

  return (
    <div className="tab-panel">
      <SectionHeader num="05 /" title="Intelligence Alerts" sub="Signal monitoring & disruption warnings" />

      <EditorialRow cols="2fr 1fr">
        <Panel>
          <PanelLabel>All Signals</PanelLabel>
          <PanelTitle>Active Alerts</PanelTitle>
          <div style={{ maxHeight: 500, overflowY: 'auto' }}>
            {(alerts || []).map((a, i) => <AlertItem key={i} alert={a} />)}
          </div>
        </Panel>

        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <Panel style={{ flex: 1, borderBottom: '1px solid var(--rule)' }}>
            <PanelLabel>By Alert Type</PanelLabel>
            <PanelTitle style={{ fontSize: 17 }}>Distribution</PanelTitle>
            <div style={{ height: 180 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={40} outerRadius={70} dataKey="value">
                    {pieData.map((_, i) => (
                      <Cell key={i} fill={PIE_FILLS[i % PIE_FILLS.length]} stroke={PIE_STROKES[i % PIE_STROKES.length]} strokeWidth={1.5} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 8, padding: 12, fontFamily: 'var(--font-m)', fontSize: 13, color: '#000000', boxShadow: '0 4px 12px rgba(0, 0, 0, 0)' }} />  
                  <Legend iconSize={12} wrapperStyle={{ fontSize: 13, fontFamily: 'var(--font-m)', paddingTop: 8 }} formatter={(value) => <span style={{ color: '#1e293b', fontWeight: 500 }}>{value}</span>} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </Panel>

          <Panel>
            <PanelLabel>By Severity Level</PanelLabel>
            <PanelTitle style={{ fontSize: 17 }}>Severity</PanelTitle>
            <div style={{ height: 180 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sevData}>
                  <CartesianGrid stroke={GRID_COLOR} strokeDasharray="3 3" />
                  <XAxis dataKey="name" {...AX} />
                  <YAxis {...AX} allowDecimals={false} />
                  <Tooltip {...TOOLTIP_STYLE} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]} isAnimationActive>
                    {sevData.map((_, i) => (
                      <Cell key={i} fill={SEV_FILLS[i % SEV_FILLS.length]} stroke={SEV_STROKES[i % SEV_STROKES.length]} strokeWidth={1.5} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Panel>
        </div>
      </EditorialRow>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════
   Main App
══════════════════════════════════════════════════════════ */
const TABS = ['Overview', 'Forecast', 'Skills', 'Resume', 'Alerts'];

export default function App() {
  const [tab, setTab] = useState('Overview');
  const [summary, setSummary] = useState(null);
  const [skills, setSkills] = useState([]);
  const [trending, setTrending] = useState([]);
  const [emerging, setEmerging] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState(null);
  const [clock, setClock] = useState('');

  /* Clock */
  useEffect(() => {
    const tick = () => {
      const n = new Date();
      setClock(
        n.toLocaleDateString('en-IN', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' }) +
        ' · ' +
        n.toLocaleTimeString('en-IN', { hour12: false })
      );
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  /* Data */
  useEffect(() => {
    Promise.all([
      api.getSummary(),
      api.getSkills('?limit=200'),
      api.getTrending(),
      api.getEmerging(),
      api.getAlerts(),
    ]).then(([sum, sk, tr, em, al]) => {
      setSummary(sum);
      setSkills(sk.skills || []);
      setTrending(tr.trending || []);
      setEmerging(em.emerging || []);
      setAlerts(al.alerts || []);
    }).catch(e => setError(e.message));
  }, []);

  return (
    <>
      <StyleTag />

      {/* ── HEADER ── */}
      <header style={{ background: '#ffffff', position: 'sticky', top: 0, zIndex: 500, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
        {/* Top bar */}
        <div style={{
          borderBottom: '1px solid #e2e8f0',
          padding: '10px 32px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <span style={{ fontFamily: 'var(--font-m)', fontSize: 12, color: '#030303', letterSpacing: '.08em', textTransform: 'uppercase', fontWeight: 500 }}>
            ASIE / Skill Intelligence Platform / v1.0
          </span>
          <span style={{ fontFamily: 'var(--font-m)', fontSize: 13, color: '#2563eb', letterSpacing: '.04em', fontWeight: 500 }}>
            {clock}
          </span>
        </div>

        {/* Main nav bar */}
        <div style={{ padding: '0 32px', display: 'flex', alignItems: 'center' }}>
          {/* Brand */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 16,
            padding: '14px 28px 14px 0',
            borderRight: '1px solid #e2e8f0',
            marginRight: 28, flexShrink: 0,
          }}>
            <img src="logo.png" alt="ASIE" style={{
              width: 38, height: 38, borderRadius: 8,
              objectFit: 'cover',
            }} />
            <div>
              <div style={{ fontSize: 20, fontWeight: 800, color: '#0f172a', letterSpacing: '-.02em', lineHeight: 1 }}>ASIE</div>
              <div style={{ fontFamily: 'var(--font-m)', fontSize: 11, color: '#000000', letterSpacing: '.06em', textTransform: 'uppercase', marginTop: 3 }}>
                Adaptive Skill Intelligence Engine
              </div>
            </div>
          </div>

          {/* Nav */}
          <nav style={{ display: 'flex' }}>
            {TABS.map(t => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`nav-btn${tab === t ? ' active' : ''}`}
                style={{
                  padding: '18px 22px', background: 'transparent', border: 'none',
                  color: tab === t ? '#0f172a' : '#6450ffe0',
                  fontFamily: 'var(--font-d)', fontSize: 14, fontWeight: 600,
                  letterSpacing: '.03em', textTransform: 'uppercase',
                  cursor: 'pointer',
                }}
              >
                {t}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* ── MAIN ── */}
      <main style={{ maxWidth: 1480, margin: '0 auto', padding: '0 32px 48px', position: 'relative', zIndex: 1 }}>

        {error && (
          <div style={{
            margin: '20px 0', padding: '16px 20px',
            border: '1px solid #fecaca', borderRadius: 'var(--r)',
            background: '#fef2f2',
          }}>
            <p style={{ color: '#dc2626', fontSize: 15 }}>Failed to load data: {error}</p>
            <p style={{ fontSize: 13, color: 'var(--text-m)', marginTop: 4 }}>
              Make sure to run <code style={{ color: '#16a34a' }}>python -m asie.seed</code> and start the API server.
            </p>
          </div>
        )}

        {tab === 'Overview' && <OverviewTab summary={summary} trending={trending} emerging={emerging} alerts={alerts} />}
        {tab === 'Forecast' && <ForecastTab skills={skills} />}
        {tab === 'Skills' && <SkillsTableTab skills={skills} />}
        {tab === 'Resume' && <ResumeTab />}
        {tab === 'Alerts' && <AlertsTab alerts={alerts} />}
      </main>

      {/* ── FOOTER ── */}
      <footer style={{
        background: '#ffffff', color: '#64748b',
        padding: '20px 32px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '0 auto',
        borderTop: '1px solid #e2e8f0',
      }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: '#0f172a', display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="dot-live" />
          ASIE — Adaptive Skill Intelligence Engine
        </div>
        <div style={{ fontFamily: 'var(--font-m)', fontSize: 12, letterSpacing: '.04em', color: '#94a3b8' }}>
          v1.0.0 · {new Date().getFullYear()} · All signals simulated
        </div>
      </footer>
    </>
  );
}