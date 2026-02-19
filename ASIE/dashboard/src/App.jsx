import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, AreaChart, Area, Cell,
  PieChart, Pie, Legend,
} from 'recharts';
import { api } from './api';

/* ── Utility helpers ───────────────────────────────────── */
const pct  = v => `${(v * 100).toFixed(1)}%`;
const fmt  = v => typeof v === 'number' ? v.toFixed(3) : v;
const cls  = (...c) => c.filter(Boolean).join(' ');

const COLORS = ['#3b82f6','#8b5cf6','#10b981','#f59e0b','#ef4444','#06b6d4','#ec4899','#14b8a6'];

const riskColor = v => v > 0.6 ? 'text-red-400' : v > 0.35 ? 'text-amber-400' : 'text-emerald-400';
const growthColor = v => v > 0.65 ? 'text-emerald-400' : v > 0.4 ? 'text-blue-400' : 'text-red-400';

/* ── Reusable Components ───────────────────────────────── */

function ScoreBar({ value, color = 'bg-blue-500', label }) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="w-28 text-surface-200 truncate">{label}</span>
      <div className="flex-1 bg-surface-700 rounded-full h-2">
        <div className={`score-bar ${color}`} style={{ width: `${Math.min(value * 100, 100)}%` }} />
      </div>
      <span className="w-12 text-right text-xs text-surface-200">{pct(value)}</span>
    </div>
  );
}

function StatCard({ title, value, subtitle, accent = 'text-blue-400' }) {
  return (
    <div className="card glow text-center">
      <p className="text-xs uppercase tracking-wider text-surface-200 mb-1">{title}</p>
      <p className={`text-2xl font-bold ${accent}`}>{value}</p>
      {subtitle && <p className="text-xs text-surface-200 mt-1">{subtitle}</p>}
    </div>
  );
}

function AlertBadge({ type }) {
  const map = {
    momentum_spike: 'badge-blue',
    bubble_warning: 'badge-yellow',
    emerging_skill: 'badge-green',
    declining_skill: 'badge-red',
    disruption: 'badge-purple',
  };
  return <span className={`badge ${map[type] || 'badge-blue'}`}>{type.replace('_', ' ')}</span>;
}

/* ── TAB: Overview Dashboard ───────────────────────────── */

function OverviewTab({ summary, trending, emerging, alerts }) {
  if (!summary) return <p className="text-surface-200">Loading...</p>;

  const topGrowing = summary.top_growing || [];
  const highestRisk = summary.highest_risk || [];

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard title="Skills Tracked" value={summary.total_skills_tracked} accent="text-blue-400" />
        <StatCard title="Avg Growth" value={pct(summary.avg_growth_score)} accent="text-emerald-400" />
        <StatCard title="Avg Automation Risk" value={pct(summary.avg_automation_risk)} accent="text-amber-400" />
        <StatCard title="Active Alerts" value={summary.active_alerts} accent="text-red-400" />
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Top Growing Skills */}
        <div className="card">
          <h3 className="text-sm font-semibold text-surface-200 mb-4 uppercase tracking-wider">Top Growing Skills</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={topGrowing} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis type="number" domain={[0, 1]} tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis type="category" dataKey="name" tick={{ fill: '#e2e8f0', fontSize: 11 }} width={130} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
              <Bar dataKey="growth" fill="#10b981" radius={[0, 4, 4, 0]}>
                {topGrowing.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Highest Automation Risk */}
        <div className="card">
          <h3 className="text-sm font-semibold text-surface-200 mb-4 uppercase tracking-wider">Highest Automation Risk</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={highestRisk} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis type="number" domain={[0, 1]} tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis type="category" dataKey="name" tick={{ fill: '#e2e8f0', fontSize: 11 }} width={130} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
              <Bar dataKey="risk" fill="#ef4444" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Trending & Emerging side-by-side */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-sm font-semibold text-surface-200 mb-3 uppercase tracking-wider">Trending (by Momentum)</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto pr-2">
            {(trending || []).map((s, i) => (
              <div key={s.skill_id} className="flex items-center justify-between text-sm">
                <span className="text-surface-200">{i + 1}. {s.name}</span>
                <span className="font-mono text-xs text-blue-400">{fmt(s.momentum_index)}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="card">
          <h3 className="text-sm font-semibold text-surface-200 mb-3 uppercase tracking-wider">Emerging Skills</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto pr-2">
            {(emerging || []).map((s, i) => (
              <div key={s.skill_id} className="flex items-center justify-between text-sm">
                <span className="text-surface-200">{i + 1}. {s.name}</span>
                <span className="font-mono text-xs text-emerald-400">{fmt(s.emergence_score)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Alert Feed */}
      <div className="card">
        <h3 className="text-sm font-semibold text-surface-200 mb-3 uppercase tracking-wider">Recent Alerts</h3>
        <div className="space-y-3 max-h-72 overflow-y-auto pr-2">
          {(alerts || []).slice(0, 10).map((a, i) => (
            <div key={i} className="flex items-start gap-3 text-sm border-b border-surface-700 pb-2">
              <AlertBadge type={a.alert_type} />
              <p className="text-surface-200 flex-1">{a.message?.slice(0, 150)}...</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ── TAB: Skill Detail / Forecast ──────────────────────── */

function ForecastTab({ skills }) {
  const [selected, setSelected] = useState(null);
  const [forecast, setForecast] = useState(null);

  useEffect(() => {
    if (selected) {
      api.getSkillForecast(selected).then(setForecast).catch(console.error);
    }
  }, [selected]);

  const skillList = skills || [];
  const fc = forecast?.forecast;
  const explanations = forecast?.explanations;

  // Build chart data from predicted demand
  const chartData = (fc?.predicted_demand || []).map((v, i) => ({
    month: i + 1,
    demand: parseFloat(v.toFixed(4)),
    lower: fc?.prediction_intervals?.[i]?.lower?.toFixed(4),
    upper: fc?.prediction_intervals?.[i]?.upper?.toFixed(4),
  }));

  // Radar data for scores
  const radarData = fc ? [
    { metric: 'Growth', value: fc.growth_score },
    { metric: 'Confidence', value: fc.confidence_score },
    { metric: 'Reliability', value: fc.reliability_score || 0.5 },
    { metric: '1 - Volatility', value: 1 - fc.volatility_score },
    { metric: '1 - Auto Risk', value: 1 - fc.automation_risk },
    { metric: '1 - Bubble', value: 1 - fc.bubble_score },
  ] : [];

  return (
    <div className="space-y-6">
      {/* Skill Selector */}
      <div className="card">
        <label className="text-xs uppercase tracking-wider text-surface-200">Select a Skill</label>
        <select
          className="mt-2 w-full bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 outline-none"
          value={selected || ''}
          onChange={e => setSelected(e.target.value)}
        >
          <option value="">-- choose --</option>
          {skillList.map(s => (
            <option key={s.skill_id} value={s.skill_id}>{s.name}</option>
          ))}
        </select>
      </div>

      {fc && (
        <>
          {/* Score Cards */}
          <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
            <StatCard title="Growth" value={pct(fc.growth_score)} accent={growthColor(fc.growth_score)} />
            <StatCard title="Confidence" value={pct(fc.confidence_score)} accent="text-blue-400" />
            <StatCard title="Volatility" value={pct(fc.volatility_score)} accent="text-amber-400" />
            <StatCard title="Momentum" value={fmt(fc.momentum_index)} accent="text-purple-400" />
            <StatCard title="Bubble" value={pct(fc.bubble_score)} accent="text-yellow-400" />
            <StatCard title="Auto Risk" value={pct(fc.automation_risk)} accent={riskColor(fc.automation_risk)} />
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {/* Forecast Chart */}
            <div className="card md:col-span-2">
              <h3 className="text-sm font-semibold text-surface-200 mb-3 uppercase tracking-wider">5-Year Demand Forecast</h3>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="month" tick={{ fill: '#94a3b8', fontSize: 10 }} label={{ value: 'Months', position: 'insideBottom', offset: -5, fill: '#94a3b8' }} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} />
                  <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
                  <Area type="monotone" dataKey="upper" stackId="1" stroke="none" fill="#3b82f620" />
                  <Area type="monotone" dataKey="lower" stackId="2" stroke="none" fill="#0f172a" />
                  <Line type="monotone" dataKey="demand" stroke="#3b82f6" strokeWidth={2} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Radar Chart */}
            <div className="card">
              <h3 className="text-sm font-semibold text-surface-200 mb-3 uppercase tracking-wider">Skill Health Radar</h3>
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#334155" />
                  <PolarAngleAxis dataKey="metric" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                  <PolarRadiusAxis domain={[0, 1]} tick={false} />
                  <Radar dataKey="value" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.3} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Explainability */}
          {explanations && (
            <div className="card">
              <h3 className="text-sm font-semibold text-surface-200 mb-3 uppercase tracking-wider">Forecast Explanation (SHAP)</h3>
              <p className="text-sm text-surface-200 mb-4">{explanations.narrative}</p>
              <div className="space-y-2">
                {Object.entries(explanations.feature_impacts || {}).slice(0, 8).map(([feat, impact]) => (
                  <ScoreBar key={feat} label={feat} value={impact} color="bg-purple-500" />
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

/* ── TAB: Resume Gap Analysis ──────────────────────────── */

function ResumeTab() {
  const [text, setText] = useState('');
  const [industry, setIndustry] = useState('');
  const [role, setRole] = useState('');
  const [roles, setRoles] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  // Fetch roles whenever industry changes
  useEffect(() => {
    setRole('');
    api.getRoles(industry).then(r => setRoles(r.roles || [])).catch(() => setRoles([]));
  }, [industry]);

  const analyze = async () => {
    if (!text.trim()) return;
    setLoading(true);
    try {
      const res = await api.analyzeResume({
        resume_text: text,
        target_industry: industry || null,
        target_role: role || null,
      });
      setResult(res);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const trendIcon = (outlook) =>
    outlook === 'growing' ? '🟢 Growing' : outlook === 'declining' ? '🔴 Declining' : '🟡 Stable';

  return (
    <div className="space-y-6">
      <div className="card">
        <h3 className="text-sm font-semibold text-surface-200 mb-3 uppercase tracking-wider">Paste Your Resume</h3>
        <textarea
          className="w-full h-40 bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-sm text-white focus:ring-2 focus:ring-blue-500 outline-none resize-y"
          placeholder="Paste your resume text here... (PII will be stripped automatically)"
          value={text}
          onChange={e => setText(e.target.value)}
        />
        <div className="flex flex-wrap gap-3 mt-3">
          {/* Industry select */}
          <select className="bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-sm text-white outline-none" value={industry} onChange={e => setIndustry(e.target.value)}>
            <option value="">Any Industry</option>
            {['technology','finance','healthcare','manufacturing','energy','education','retail','government'].map(i => (
              <option key={i} value={i}>{i.charAt(0).toUpperCase() + i.slice(1)}</option>
            ))}
          </select>
          {/* Role select (populated from API based on industry) */}
          <select className="bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-sm text-white outline-none min-w-[200px]" value={role} onChange={e => setRole(e.target.value)}>
            <option value="">Any Role</option>
            {roles.map(r => (
              <option key={r.role_id} value={r.role_id}>{r.display_name}</option>
            ))}
          </select>
          <button onClick={analyze} disabled={loading} className="px-5 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium disabled:opacity-50 transition">
            {loading ? 'Analysing...' : 'Analyse Gaps'}
          </button>
        </div>
        {role && roles.length > 0 && (
          <p className="text-xs text-surface-300 mt-2">
            {roles.find(r => r.role_id === role)?.description || ''}
            {' — '}
            <span className="font-medium">{trendIcon(roles.find(r => r.role_id === role)?.trend_outlook)}</span>
            {' (3-5 yr outlook)'}
          </p>
        )}
      </div>

      {result && (
        <>
          {/* KPI cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard title="Skills Found" value={result.extracted_skills?.length || 0} accent="text-blue-400" />
            <StatCard
              title={result.target_role ? 'Role Readiness' : 'Readiness'}
              value={pct(result.role_readiness_score ?? result.overall_readiness_score)}
              accent={growthColor(result.role_readiness_score ?? result.overall_readiness_score)}
              subtitle={result.target_role ? result.target_role.replace(/_/g, ' ') : undefined}
            />
            <StatCard title="Gaps Found" value={result.skill_gaps?.length || 0} accent="text-amber-400" />
            <StatCard title="Recommended" value={result.top_recommended_skills?.length || 0} accent="text-purple-400" />
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Skill Gaps with future trend */}
            <div className="card">
              <h3 className="text-sm font-semibold text-surface-200 mb-3 uppercase tracking-wider">
                Skill Gaps {result.target_role ? `for ${result.target_role.replace(/_/g, ' ')}` : '(by priority)'}
              </h3>
              <div className="space-y-2 max-h-80 overflow-y-auto pr-2">
                {(result.skill_gaps || []).map((g, i) => (
                  <div key={i} className="border-b border-surface-700 pb-2">
                    <div className="flex justify-between text-sm">
                      <span className="font-medium">{g.skill_name.replace(/_/g, ' ')}</span>
                      <span className={`badge ${g.priority === 'critical' ? 'badge-red' : g.priority === 'high' ? 'badge-yellow' : 'badge-blue'}`}>{g.priority}</span>
                    </div>
                    <ScoreBar label="Gap" value={g.gap_score} color="bg-red-500" />
                    {g.future_trend && (
                      <p className="text-xs text-surface-300 mt-0.5">{g.future_trend}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Role Fit Ranking OR Industry Fit */}
            <div className="card">
              {(result.role_fit_results && result.role_fit_results.length > 0) ? (
                <>
                  <h3 className="text-sm font-semibold text-surface-200 mb-3 uppercase tracking-wider">Best-Fit Roles for You</h3>
                  <div className="space-y-2 max-h-80 overflow-y-auto pr-2">
                    {result.role_fit_results.map((rf, i) => (
                      <div key={i} className="border-b border-surface-700 pb-2">
                        <div className="flex justify-between items-center text-sm">
                          <div>
                            <span className="font-medium">{rf.role_name}</span>
                            <span className="ml-2 text-xs text-surface-300">{trendIcon(rf.trend_outlook)}</span>
                          </div>
                          <span className={`text-sm font-bold ${growthColor(rf.readiness_score)}`}>{pct(rf.readiness_score)}</span>
                        </div>
                        <ScoreBar label="Fit" value={rf.readiness_score} color={rf.readiness_score > 0.6 ? 'bg-emerald-500' : rf.readiness_score > 0.3 ? 'bg-amber-500' : 'bg-red-500'} />
                        {rf.missing_required.length > 0 && (
                          <p className="text-xs text-red-400 mt-0.5">Missing: {rf.missing_required.map(s => s.replace(/_/g, ' ')).join(', ')}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <>
                  <h3 className="text-sm font-semibold text-surface-200 mb-3 uppercase tracking-wider">Industry Fit</h3>
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={Object.entries(result.industry_fit || {}).map(([k, v]) => ({ industry: k, fit: v }))}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="industry" tick={{ fill: '#94a3b8', fontSize: 10 }} angle={-30} textAnchor="end" height={60} />
                      <YAxis domain={[0, 1]} tick={{ fill: '#94a3b8', fontSize: 10 }} />
                      <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
                      <Bar dataKey="fit" fill="#8b5cf6" radius={[4, 4, 0, 0]}>
                        {Object.entries(result.industry_fit || {}).map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </>
              )}
            </div>
          </div>

          <div className="card">
            <h3 className="text-sm font-semibold text-surface-200 mb-3 uppercase tracking-wider">Recommended Skills to Learn</h3>
            <div className="flex flex-wrap gap-2">
              {(result.top_recommended_skills || []).map((s, i) => (
                <span key={i} className="badge badge-green text-sm">{s.replace(/_/g, ' ')}</span>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

/* ── TAB: All Skills Table ─────────────────────────────── */

function SkillsTableTab({ skills }) {
  const [sort, setSort] = useState('growth_score');
  const [dir, setDir] = useState(-1);
  const [filter, setFilter] = useState('');

  const toggleSort = col => {
    if (sort === col) setDir(d => d * -1);
    else { setSort(col); setDir(-1); }
  };

  const filtered = (skills || [])
    .filter(s => s.name.toLowerCase().includes(filter.toLowerCase()))
    .sort((a, b) => (a[sort] - b[sort]) * dir);

  const hdr = (label, col) => (
    <th className="px-3 py-2 cursor-pointer hover:text-blue-400 select-none" onClick={() => toggleSort(col)}>
      {label} {sort === col ? (dir > 0 ? '↑' : '↓') : ''}
    </th>
  );

  return (
    <div className="card overflow-x-auto">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-surface-200 uppercase tracking-wider">All Skills</h3>
        <input
          className="bg-surface-700 border border-surface-600 rounded-lg px-3 py-1.5 text-sm text-white outline-none w-56"
          placeholder="Search skills..."
          value={filter}
          onChange={e => setFilter(e.target.value)}
        />
      </div>
      <table className="w-full text-sm">
        <thead className="text-xs uppercase text-surface-200 border-b border-surface-700">
          <tr>
            <th className="px-3 py-2 text-left">Skill</th>
            <th className="px-3 py-2">Category</th>
            {hdr('Growth', 'growth_score')}
            {hdr('Confidence', 'confidence_score')}
            {hdr('Volatility', 'volatility_score')}
            {hdr('Momentum', 'momentum_index')}
            {hdr('Bubble', 'bubble_score')}
            {hdr('Auto Risk', 'automation_risk')}
          </tr>
        </thead>
        <tbody>
          {filtered.map(s => (
            <tr key={s.skill_id} className="border-b border-surface-700/50 hover:bg-surface-700/30 transition">
              <td className="px-3 py-2 font-medium">{s.name}</td>
              <td className="px-3 py-2 text-center"><span className="badge badge-blue">{s.category}</span></td>
              <td className={`px-3 py-2 text-center font-mono ${growthColor(s.growth_score)}`}>{pct(s.growth_score)}</td>
              <td className="px-3 py-2 text-center font-mono">{pct(s.confidence_score)}</td>
              <td className="px-3 py-2 text-center font-mono">{pct(s.volatility_score)}</td>
              <td className="px-3 py-2 text-center font-mono text-purple-400">{fmt(s.momentum_index)}</td>
              <td className="px-3 py-2 text-center font-mono">{pct(s.bubble_score)}</td>
              <td className={`px-3 py-2 text-center font-mono ${riskColor(s.automation_risk)}`}>{pct(s.automation_risk)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ── TAB: Alerts ───────────────────────────────────────── */

function AlertsTab({ alerts }) {
  const grouped = {};
  (alerts || []).forEach(a => {
    grouped[a.alert_type] = grouped[a.alert_type] || [];
    grouped[a.alert_type].push(a);
  });

  const pieData = Object.entries(grouped).map(([type, arr]) => ({ name: type.replace('_',' '), value: arr.length }));

  return (
    <div className="space-y-6">
      <div className="grid md:grid-cols-3 gap-6">
        <div className="card md:col-span-2">
          <h3 className="text-sm font-semibold text-surface-200 mb-3 uppercase tracking-wider">All Alerts</h3>
          <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
            {(alerts || []).map((a, i) => (
              <div key={i} className="border-b border-surface-700 pb-3">
                <div className="flex items-center gap-2 mb-1">
                  <AlertBadge type={a.alert_type} />
                  <span className={`badge ${a.severity === 'critical' ? 'badge-red' : a.severity === 'high' ? 'badge-yellow' : 'badge-blue'}`}>{a.severity}</span>
                  <span className="text-xs text-surface-200 ml-auto">{a.skill_name?.replace(/_/g, ' ')}</span>
                </div>
                <p className="text-sm text-surface-200">{a.message}</p>
              </div>
            ))}
          </div>
        </div>
        <div className="card">
          <h3 className="text-sm font-semibold text-surface-200 mb-3 uppercase tracking-wider">Alert Distribution</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={90} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

/* ── Main App ──────────────────────────────────────────── */

const TABS = ['Overview', 'Forecast', 'Skills', 'Resume', 'Alerts'];

export default function App() {
  const [tab, setTab] = useState('Overview');
  const [summary, setSummary] = useState(null);
  const [skills, setSkills] = useState([]);
  const [trending, setTrending] = useState([]);
  const [emerging, setEmerging] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([
      api.getSummary(),
      api.getSkills('?limit=200'),
      api.getTrending(),
      api.getEmerging(),
      api.getAlerts(),
    ])
      .then(([sum, sk, tr, em, al]) => {
        setSummary(sum);
        setSkills(sk.skills || []);
        setTrending(tr.trending || []);
        setEmerging(em.emerging || []);
        setAlerts(al.alerts || []);
      })
      .catch(e => setError(e.message));
  }, []);

  return (
    <div className="min-h-screen bg-surface-900">
      {/* Header */}
      <header className="border-b border-surface-700 bg-surface-800/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🧠</span>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight">ASIE</h1>
              <p className="text-xs text-surface-200">Adaptive Skill Intelligence Engine</p>
            </div>
          </div>
          <nav className="flex gap-1">
            {TABS.map(t => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={cls(
                  'px-4 py-2 rounded-lg text-sm font-medium transition',
                  tab === t ? 'bg-blue-600 text-white' : 'text-surface-200 hover:bg-surface-700'
                )}
              >
                {t}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {error && (
          <div className="card border-red-700 bg-red-900/20 mb-6">
            <p className="text-red-400 text-sm">Failed to load data: {error}</p>
            <p className="text-xs text-surface-200 mt-1">Make sure to run <code className="text-blue-400">python -m asie.seed</code> and start the API server.</p>
          </div>
        )}

        {tab === 'Overview'  && <OverviewTab summary={summary} trending={trending} emerging={emerging} alerts={alerts} />}
        {tab === 'Forecast'  && <ForecastTab skills={skills} />}
        {tab === 'Skills'    && <SkillsTableTab skills={skills} />}
        {tab === 'Resume'    && <ResumeTab />}
        {tab === 'Alerts'    && <AlertsTab alerts={alerts} />}
      </main>

      {/* Footer */}
      <footer className="border-t border-surface-700 mt-10 py-4 text-center text-xs text-surface-200">
        ASIE v1.0.0 · Adaptive Skill Intelligence Engine · {new Date().getFullYear()}
      </footer>
    </div>
  );
}
