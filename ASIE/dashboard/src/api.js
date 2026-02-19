const BASE = '/api/v1';

async function fetchJSON(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  getSkills:      (params = '')  => fetchJSON(`/skills${params}`),
  getSkillForecast: (id)         => fetchJSON(`/skills/${id}/forecast`),
  getTrending:    (limit = 15)   => fetchJSON(`/skills/trending?limit=${limit}`),
  getEmerging:    (limit = 10)   => fetchJSON(`/skills/emerging?limit=${limit}`),
  getAtRisk:      (limit = 15)   => fetchJSON(`/skills/at-risk?limit=${limit}`),
  getAlerts:      (params = '')  => fetchJSON(`/alerts${params}`),
  getSummary:     ()             => fetchJSON(`/dashboard/summary`),
  getGraph:       ()             => fetchJSON(`/graph`),
  getNeighbors:   (id, depth=1)  => fetchJSON(`/graph/neighbors/${id}?depth=${depth}`),
  getLearningPath:(from, to)     => fetchJSON(`/graph/learning-path?from_skill=${from}&to_skill=${to}`),
  filterByGeo:    (geo)          => fetchJSON(`/filters/geo?geo=${geo}`),
  filterByIndustry:(ind)         => fetchJSON(`/filters/industry?industry=${ind}`),
  getRoles:       (industry='')  => fetchJSON(`/roles${industry ? `?industry=${industry}` : ''}`),
  analyzeResume:  (body)         => fetch(`${BASE}/resume/analyze`, {
    method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body)
  }).then(r => r.json()),
  uploadResume:   (file, opts={}) => {
    const fd = new FormData();
    fd.append('file', file);
    if (opts.target_industry) fd.append('target_industry', opts.target_industry);
    if (opts.target_role) fd.append('target_role', opts.target_role);
    if (opts.target_geo) fd.append('target_geo', opts.target_geo);
    return fetch(`${BASE}/resume/upload`, { method: 'POST', body: fd }).then(r => {
      if (!r.ok) return r.json().then(e => { throw new Error(e.detail || 'Upload failed'); });
      return r.json();
    });
  },
};
