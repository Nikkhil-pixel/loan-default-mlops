import { useEffect, useState } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'https://loan-default-mlops-api.onrender.com'

const initialForm = {
  person_age: 30,
  person_income: 60000,
  person_home_ownership: 'RENT',
  person_emp_length: 5,
  loan_intent: 'PERSONAL',
  loan_grade: 'B',
  loan_amnt: 10000,
  loan_int_rate: 11,
  loan_percent_income: 16.67,
  cb_person_default_on_file: 'N',
  cb_person_cred_hist_length: 6,
}

const featureGroups = [
  {
    title: 'Personal profile',
    description: 'Basic applicant information',
    fields: [
      { name: 'person_age', label: 'Age', type: 'number', min: 18, max: 80, step: 1, suffix: 'years' },
      { name: 'person_income', label: 'Annual income', type: 'number', min: 0, max: 6000000, step: 1000, prefix: '$' },
      { name: 'person_emp_length', label: 'Employment length', type: 'number', min: 0, max: 64, step: 1, suffix: 'years' },
      { name: 'person_home_ownership', label: 'Home ownership', options: ['RENT', 'OWN', 'MORTGAGE', 'OTHER'] },
      { name: 'cb_person_cred_hist_length', label: 'Credit history length', type: 'number', min: 0, max: 100, step: 1, suffix: 'years' },
      { name: 'cb_person_default_on_file', label: 'Previous default on file', options: ['N', 'Y'] },
    ],
  },
  {
    title: 'Loan details',
    description: 'Information about the requested loan',
    fields: [
      { name: 'loan_amnt', label: 'Loan amount', type: 'number', min: 0, max: 1000000, step: 500, prefix: '$' },
      { name: 'loan_int_rate', label: 'Interest rate', type: 'number', min: 0, max: 100, step: 0.1, suffix: '%' },
      { name: 'loan_percent_income', label: 'Loan-to-income ratio', type: 'number', min: 0, max: 100, step: 0.1, suffix: '%' },
      { name: 'loan_intent', label: 'Loan purpose', options: ['PERSONAL', 'EDUCATION', 'MEDICAL', 'VENTURE', 'HOMEIMPROVEMENT', 'DEBTCONSOLIDATION'] },
      { name: 'loan_grade', label: 'Loan grade', options: ['A', 'B', 'C', 'D', 'E', 'F', 'G'] },
    ],
  },
]

async function fetchJson(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
  })

  const body = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(body.detail || `Request failed (${response.status})`)
  }

  return body
}

function Icon({ name, size = 20 }) {
  const common = {
    width: size,
    height: size,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.7,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
    'aria-hidden': true,
  }

  const paths = {
    grid: <><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /></>,
    plus: <><path d="M12 5v14" /><path d="M5 12h14" /></>,
    clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
    activity: <><path d="M3 12h4l3-8 4 16 3-8h4" /></>,
    settings: <><circle cx="12" cy="12" r="3" /><path d="m19.4 15 .1.1 1.4 1.1-1.4 2.4-1.7-.6a8 8 0 0 1-1.8 1l-.3 1.8h-2.8l-.3-1.8a8 8 0 0 1-1.8-1l-1.7.6-1.4-2.4L7.1 15a8 8 0 0 1 0-2l-1.4-1.1 1.4-2.4 1.7.6a8 8 0 0 1 1.8-1l.3-1.8h2.8l.3 1.8a8 8 0 0 1 1.8 1l1.7-.6 1.4 2.4-1.4 1.1a8 8 0 0 1-.1 2Z" /></>,
    shield: <><path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z" /><path d="m9 12 2 2 4-4" /></>,
    arrow: <><path d="M7 17 17 7" /><path d="M7 7h10v10" /></>,
    refresh: <><path d="M20 7v5h-5" /><path d="M4 17v-5h5" /><path d="M5.6 9a7 7 0 0 1 11.6-2L20 12M4 12l2.8 5a7 7 0 0 0 11.6-2" /></>,
    check: <path d="m5 12 4 4L19 6" />,
    alert: <><path d="M12 9v4" /><path d="M12 17h.01" /><path d="M10.3 3.9 2 18.2A2 2 0 0 0 3.7 21h16.6a2 2 0 0 0 1.7-2.8L13.7 3.9a2 2 0 0 0-3.4 0Z" /></>,
    sliders: <><path d="M4 21v-7m0-4V3m8 18v-9m0-4V3m8 18v-5m0-4V3M2 14h4m4-6h4m4 8h4" /></>,
  }

  return <svg {...common}>{paths[name] || paths.grid}</svg>
}

function Sidebar({ active, onNavigate, apiStatus }) {
  const items = [
    { id: 'overview', label: 'Overview', icon: 'grid' },
    { id: 'assessment', label: 'New assessment', icon: 'plus' },
    { id: 'history', label: 'Assessment history', icon: 'clock' },
    { id: 'monitoring', label: 'Model monitoring', icon: 'activity' },
  ]

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark"><Icon name="shield" size={23} /></div>
        <div><strong>risk<span>lens</span></strong><small>ML RISK INTELLIGENCE</small></div>
      </div>

      <div className="workspace-label">WORKSPACE</div>
      <nav className="side-nav" aria-label="Main navigation">
        {items.map(item => (
          <button key={item.id} className={`nav-item ${active === item.id ? 'active' : ''}`} onClick={() => onNavigate(item.id)}>
            <Icon name={item.icon} size={19} />
            <span>{item.label}</span>
            {item.id === 'assessment' && <span className="nav-add">+</span>}
          </button>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <div className="connection-card">
          <div className="connection-title"><span className={`status-dot ${apiStatus === 'online' ? 'green' : apiStatus === 'checking' ? 'amber' : 'red'}`} />API connection</div>
          <p>{apiStatus === 'online' ? 'Backend reachable' : apiStatus === 'checking' ? 'Checking backend…' : 'Backend unavailable'}</p>
          <code>Render API</code>
        </div>
        <button className={`nav-item ${active === 'settings' ? 'active' : ''}`} onClick={() => onNavigate('settings')}><Icon name="settings" size={19} /><span>Configuration</span></button>
        <div className="profile">
          <div className="avatar">RL</div>
          <div className="profile-text"><strong>RiskLens workspace</strong><small>Loan risk project</small></div>
          <span className="profile-menu">•••</span>
        </div>
      </div>
    </aside>
  )
}

function Topbar({ active, onRefresh, refreshing }) {
  const titles = {
    overview: ['Overview', 'Your model serving and risk assessment workspace.'],
    assessment: ['New assessment', 'Evaluate a loan application using the active champion model.'],
    history: ['Assessment history', 'Review assessments recorded during this session.'],
    monitoring: ['Model monitoring', 'Inspect API health and registered model information.'],
    settings: ['Configuration', 'Review the connection settings for this workspace.'],
  }

  const [title, subtitle] = titles[active] || titles.overview

  return (
    <header className="topbar">
      <div className="breadcrumbs"><span>Workspace</span><span className="crumb-slash">/</span><strong>{title}</strong></div>
      <div className="topbar-right">
        <span className="environment-tag"><span className="environment-dot" /> LOCAL ENVIRONMENT</span>
        <button className="icon-button" onClick={onRefresh} disabled={refreshing} title="Refresh backend status" aria-label="Refresh backend status">
          <Icon name="refresh" size={17} />
        </button>
        <div className="topbar-avatar">RL</div>
      </div>
      <div className="page-heading"><h1>{title}</h1><p>{subtitle}</p></div>
    </header>
  )
}

function MetricCard({ label, value, note, icon, tone = '' }) {
  return (
    <article className="metric-card">
      <div className={`metric-icon ${tone}`}><Icon name={icon} size={19} /></div>
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      <div className="metric-note">{note}</div>
    </article>
  )
}

function StatusPill({ online, children }) {
  return <span className={`status-pill ${online ? 'success' : 'warning'}`}><span />{children}</span>
}

function Overview({ health, modelInfo, assessments, apiStatus, onNavigate }) {
  const latest = assessments[0]

  return (
    <>
      <section className="welcome-banner">
        <div className="welcome-copy">
          <span className="eyebrow light">LOAN DEFAULT PREDICTION · MLOPS</span>
          <h2>Make every assessment<br />a little more <em>insightful.</em></h2>
          <p>Evaluate applicant risk with your registered machine learning model and keep track of model serving health.</p>
          <button className="button button-white" onClick={() => onNavigate('assessment')}>New assessment <Icon name="arrow" size={16} /></button>
        </div>
        <div className="banner-graphic" aria-hidden="true">
          <div className="orbit orbit-one" /><div className="orbit orbit-two" />
          <div className="graphic-core"><Icon name="shield" size={45} /></div>
          <div className="graphic-chip chip-one"><span className="chip-dot" /> ML MODEL</div>
          <div className="graphic-chip chip-two"><Icon name="activity" size={16} /> RISK SIGNALS</div>
          <div className="graphic-node node-one" /><div className="graphic-node node-two" /><div className="graphic-node node-three" />
        </div>
      </section>

      <div className="section-heading">
        <div><h2>Workspace status</h2><p>Live information from your local API</p></div>
        <span className="live-label"><span /> LIVE CONNECTION</span>
      </div>

      <section className="metrics-grid">
        <MetricCard label="API status" value={apiStatus === 'online' ? 'Connected' : apiStatus === 'checking' ? 'Checking' : 'Offline'} note={health?.status === 'ok' ? 'Health endpoint responding' : 'Check backend availability'} icon="activity" tone="mint" />
        <MetricCard label="Champion model" value={modelInfo?.version ? `Version ${modelInfo.version}` : 'Unavailable'} note={modelInfo?.model_name || 'No model information returned'} icon="shield" tone="lavender" />
        <MetricCard label="Session assessments" value={String(assessments.length)} note="Successful predictions this session" icon="grid" tone="peach" />
        <MetricCard label="Latest risk band" value={latest ? latest.risk_band.toUpperCase() : '—'} note={latest ? 'From latest successful prediction' : 'Run an assessment to see a result'} icon="activity" tone="blue" />
      </section>

      <section className="overview-lower">
        <article className="panel model-panel">
          <div className="panel-heading"><div><h3>Model serving</h3><p>Current champion registry details</p></div><Icon name="shield" size={21} /></div>
          <div className="model-status-row"><div className="model-symbol"><Icon name="activity" size={22} /></div><div className="model-name"><strong>{modelInfo?.model_name || 'Model information unavailable'}</strong><span>Registry champion alias</span></div><StatusPill online={Boolean(modelInfo?.version)}>{modelInfo?.version ? 'Loaded' : 'Unavailable'}</StatusPill></div>
          <div className="detail-list">
            <div><span>Model version</span><strong>{modelInfo?.version || '—'}</strong></div>
            <div><span>Registry alias</span><strong>{modelInfo?.alias || '—'}</strong></div>
            <div><span>Data version</span><strong>{modelInfo?.data_version || '—'}</strong></div>
            <div><span>Run ID</span><strong className="run-id">{modelInfo?.run_id || '—'}</strong></div>
          </div>
          {!modelInfo && <p className="inline-note">Model details appear here when the API and MLflow registry are available.</p>}
        </article>

        <article className="panel quick-panel">
          <div className="panel-heading"><div><h3>Quick actions</h3><p>Jump into your workflow</p></div><Icon name="arrow" size={20} /></div>
          <button className="quick-action" onClick={() => onNavigate('assessment')}><div className="quick-icon mint"><Icon name="plus" size={19} /></div><div><strong>Assess an applicant</strong><span>Submit loan details for scoring</span></div><Icon name="arrow" size={17} /></button>
          <button className="quick-action" onClick={() => onNavigate('history')}><div className="quick-icon lavender"><Icon name="clock" size={19} /></div><div><strong>View session history</strong><span>Review your completed assessments</span></div><Icon name="arrow" size={17} /></button>
          <button className="quick-action" onClick={() => onNavigate('monitoring')}><div className="quick-icon peach"><Icon name="activity" size={19} /></div><div><strong>Check model health</strong><span>Inspect API and registry status</span></div><Icon name="arrow" size={17} /></button>
        </article>
      </section>

      <section className="panel recent-panel">
        <div className="panel-heading"><div><h3>Recent assessments</h3><p>Only real successful API predictions are listed</p></div><button className="text-button" onClick={() => onNavigate('history')}>View history <Icon name="arrow" size={15} /></button></div>
        {latest ? <AssessmentTable assessments={assessments.slice(0, 4)} /> : <EmptyState icon="clock" title="No assessments yet" description="Once you submit an application and receive a successful API response, the result will appear here." action="Start an assessment" onAction={() => onNavigate('assessment')} />}
      </section>
    </>
  )
}

function EmptyState({ icon, title, description, action, onAction }) {
  return <div className="empty-state"><div className="empty-icon"><Icon name={icon} size={23} /></div><h3>{title}</h3><p>{description}</p>{action && <button className="button button-primary" onClick={onAction}>{action}</button>}</div>
}

function AssessmentTable({ assessments }) {
  return (
    <div className="table-wrap"><table><thead><tr><th>Assessment</th><th>Time</th><th>Default probability</th><th>Risk band</th><th>Decision flag</th></tr></thead>
      <tbody>{assessments.map(item => <tr key={item.id}><td><strong>{item.id}</strong><small>Model v{item.model_version || '—'}</small></td><td>{item.time}</td><td><strong>{(item.default_probability * 100).toFixed(2)}%</strong></td><td><span className={`risk-tag ${item.risk_band}`}>{item.risk_band}</span></td><td><span className={`decision-tag ${item.decision_flag ? 'flagged' : 'clear'}`}>{item.decision_flag ? 'Flagged' : 'Not flagged'}</span></td></tr>)}</tbody>
    </table></div>
  )
}

function LoanAssessment({ onResult, busy, result, error, clearResult }) {
  const [form, setForm] = useState(initialForm)
  const [validationError, setValidationError] = useState('')

  function updateField(name, value) {
    setForm(current => {
      const next = { ...current, [name]: value }
      if (name === 'loan_amnt' || name === 'person_income') {
        next.loan_percent_income = next.person_income > 0
          ? Number(((next.loan_amnt / next.person_income) * 100).toFixed(2))
          : 0
      }
      return next
    })
    clearResult()
    setValidationError('')
  }

  async function submit(event) {
    event.preventDefault()
    const payload = { ...form }
    for (const field of featureGroups.flatMap(group => group.fields)) {
      if (field.type === 'number') {
        payload[field.name] = Number(payload[field.name])
        if (!Number.isFinite(payload[field.name]) || payload[field.name] < field.min || payload[field.name] > field.max) {
          setValidationError(`${field.label} must be between ${field.min} and ${field.max}.`)
          return
        }
      }
    }
    if (payload.person_income > 0) {
      payload.loan_percent_income = Number(((payload.loan_amnt / payload.person_income) * 100).toFixed(2))
    }
    await onResult(payload)
  }

  return (
    <div className="assessment-layout">
      <form className="panel assessment-form" onSubmit={submit}>
        <div className="form-intro"><span className="form-step">01</span><div><h3>Applicant information</h3><p>Enter the details required by your model's request schema.</p></div></div>
        {featureGroups.map(group => (
          <section className="form-group" key={group.title}>
            <div className="form-group-heading"><h4>{group.title}</h4><p>{group.description}</p></div>
            <div className="form-grid">{group.fields.map(field => (
              <label className="field" key={field.name}>
                <span className="field-label">{field.label}</span>
                {field.options ? <select value={form[field.name]} onChange={event => updateField(field.name, event.target.value)}>{field.options.map(option => <option key={option} value={option}>{option.replaceAll('_', ' ')}</option>)}</select> :
                  <span className="input-wrap">{field.prefix && <span className="input-prefix">{field.prefix}</span>}<input type="number" required min={field.min} max={field.max} step={field.step} value={form[field.name]} onChange={event => updateField(field.name, event.target.value)} />{field.suffix && <span className="input-suffix">{field.suffix}</span>}</span>}
              </label>
            ))}</div>
          </section>
        ))}
        {validationError && <div className="error-box"><Icon name="alert" size={18} />{validationError}</div>}
        {error && <div className="error-box"><Icon name="alert" size={18} />{error}</div>}
        <div className="form-footer"><span><Icon name="shield" size={16} /> Submitted to your local champion model</span><button className="button button-primary" type="submit" disabled={busy}>{busy ? 'Scoring application…' : 'Run risk assessment'} <Icon name="arrow" size={16} /></button></div>
      </form>

      <aside className="assessment-aside">
        <article className="panel aside-note"><div className="aside-note-icon"><Icon name="sliders" size={20} /></div><h3>Model input guide</h3><p>Your API validates all 11 configured features. Categorical values use the allowed options defined in your project's parameter file.</p><div className="guide-row"><span>Input fields</span><strong>11 required</strong></div><div className="guide-row"><span>Scoring endpoint</span><code>POST /predict</code></div><div className="guide-row"><span>Validation</span><strong>API + form</strong></div></article>
        <article className="panel result-panel">
          <div className="panel-heading"><div><h3>Assessment result</h3><p>Live model response</p></div><div className="result-shield"><Icon name="shield" size={20} /></div></div>
          {result ? <div className="result-content">
            <span className="result-caption">PREDICTED DEFAULT PROBABILITY</span>
            <div className="probability-value">{(result.default_probability * 100).toFixed(2)}<span>%</span></div>
            <div className="probability-track"><div className={`probability-fill ${result.risk_band}`} style={{ width: `${Math.min(100, Math.max(0, result.default_probability * 100))}%` }} /></div>
            <div className="result-meta"><span>Risk band</span><span className={`risk-tag ${result.risk_band}`}>{result.risk_band}</span></div>
            <div className="result-meta"><span>Decision threshold (0.50)</span><strong>{result.decision_flag ? 'Flagged' : 'Not flagged'}</strong></div>
            <p className="result-disclaimer">This is a model prediction, not a lending decision. Review the full application and applicable lending policies.</p>
          </div> : <EmptyState icon="activity" title="Awaiting assessment" description="Submit the form to get the probability and risk band returned by your actual model." />}
        </article>
      </aside>
    </div>
  )
}

function HistoryPage({ assessments, onNavigate }) {
  return <section className="panel history-panel"><div className="panel-heading"><div><h3>Assessment history</h3><p>Successful predictions saved in this browser session</p></div><span className="count-badge">{assessments.length} records</span></div>{assessments.length ? <AssessmentTable assessments={assessments} /> : <EmptyState icon="clock" title="Nothing here yet" description="Run a successful prediction to create your first session history record." action="Create assessment" onAction={() => onNavigate('assessment')} />}</section>
}

function MonitoringPage({ health, modelInfo, apiStatus, onRefresh, refreshing, error }) {
  return <>
    <section className="metrics-grid monitoring-metrics">
      <MetricCard label="API reachability" value={apiStatus === 'online' ? 'Online' : apiStatus === 'checking' ? 'Checking' : 'Offline'} note="GET /health" icon="activity" tone="mint" />
      <MetricCard label="Model loaded" value={health?.model_loaded ? 'Yes' : 'Unknown'} note={health?.status || 'No health response'} icon="shield" tone="lavender" />
      <MetricCard label="Champion version" value={modelInfo?.version || '—'} note={modelInfo?.model_name || 'Registry details unavailable'} icon="grid" tone="blue" />
      <MetricCard label="Data version" value={modelInfo?.data_version || '—'} note="Provided by the registry alias" icon="clock" tone="peach" />
    </section>
    <section className="panel monitoring-panel"><div className="panel-heading"><div><h3>Serving diagnostics</h3><p>Responses retrieved from your running backend</p></div><button className="button button-secondary" onClick={onRefresh} disabled={refreshing}><Icon name="refresh" size={16} /> Refresh</button></div>
      {error && <div className="error-box"><Icon name="alert" size={18} />{error}</div>}
      <div className="diagnostic-row"><div><strong>Health endpoint</strong><span>GET /health</span></div><StatusPill online={health?.status === 'ok'}>{health?.status || 'No response'}</StatusPill></div>
      <div className="diagnostic-row"><div><strong>Champion model registry</strong><span>GET /model-info</span></div><StatusPill online={Boolean(modelInfo?.version)}>{modelInfo?.version ? `Version ${modelInfo.version}` : 'Unavailable'}</StatusPill></div>
      <div className="diagnostic-row"><div><strong>Prediction service</strong><span>POST /predict</span></div><StatusPill online={apiStatus === 'online'}>{apiStatus === 'online' ? 'API reachable' : 'Not confirmed'}</StatusPill></div>
      <div className="detail-list monitoring-details">
        <div><span>Model name</span><strong>{modelInfo?.model_name || '—'}</strong></div>
        <div><span>Alias</span><strong>{modelInfo?.alias || '—'}</strong></div>
        <div><span>Run ID</span><strong className="run-id">{modelInfo?.run_id || '—'}</strong></div>
        <div><span>Data version</span><strong>{modelInfo?.data_version || '—'}</strong></div>
      </div>
      <p className="monitoring-footnote">This page reports serving health and registry metadata only. It does not claim live data drift results unless a monitoring endpoint is implemented and connected.</p>
    </section>
  </>
}

function SettingsPage({ apiUrl, setApiUrl, onSave }) {
  return <section className="panel settings-panel"><div className="panel-heading"><div><h3>API connection</h3><p>Configure the base URL for your local FastAPI backend.</p></div><Icon name="settings" size={22} /></div><form onSubmit={event => { event.preventDefault(); onSave(apiUrl) }}><label className="field"><span className="field-label">Backend base URL</span><input value={apiUrl} onChange={event => setApiUrl(event.target.value)} placeholder="http://localhost:8000" required /></label><p className="settings-hint">The current API schema uses /health, /predict, and /model-info. Changing this setting updates the frontend's requests for this browser session.</p><button className="button button-primary" type="submit">Save connection</button></form></section>
}

export default function App() {
  const [active, setActive] = useState('overview')
  const [health, setHealth] = useState(null)
  const [modelInfo, setModelInfo] = useState(null)
  const [apiStatus, setApiStatus] = useState('checking')
  const [refreshing, setRefreshing] = useState(false)
  const [assessments, setAssessments] = useState([])
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)
  const [predictionError, setPredictionError] = useState('')
  const [monitoringError, setMonitoringError] = useState('')
  const [apiUrl, setApiUrl] = useState(API_URL)
  const [connectionUrl, setConnectionUrl] = useState(API_URL)
  const [notice, setNotice] = useState('')

  async function refreshStatus(url = connectionUrl) {
    setRefreshing(true)
    setApiStatus('checking')
    setMonitoringError('')
    const normalizedUrl = url.replace(/\/+$/, '')
    const healthPromise = fetchJsonFrom(normalizedUrl, '/health')
    const modelPromise = fetchJsonFrom(normalizedUrl, '/model-info')

    const [healthResponse, modelResponse] = await Promise.allSettled([healthPromise, modelPromise])
    const healthData = healthResponse.status === 'fulfilled' ? healthResponse.value : null
    const modelData = modelResponse.status === 'fulfilled' ? modelResponse.value : null
    setHealth(healthData)
    setModelInfo(modelData)
    const online = Boolean(healthData)
    setApiStatus(online ? 'online' : 'offline')
    if (!online) setMonitoringError(healthResponse.reason?.message || 'Could not reach the FastAPI backend.')
    else if (healthData.status !== 'ok') setMonitoringError(healthData.error || 'API is responding, but the champion model is not loaded.')
    setRefreshing(false)
  }

  useEffect(() => {
    refreshStatus(connectionUrl)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [connectionUrl])

  async function runPrediction(payload) {
    setBusy(true)
    setPredictionError('')
    setResult(null)
    try {
      const prediction = await fetchJsonFrom(connectionUrl.replace(/\/+$/, ''), '/predict', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      if (typeof prediction.default_probability !== 'number' || !['low', 'medium', 'high'].includes(prediction.risk_band) || typeof prediction.decision_flag !== 'boolean') {
        throw new Error('The API response did not match the expected prediction schema.')
      }
      setResult(prediction)
      const modelVersion = modelInfo?.version || '—'
      setAssessments(current => [{
        id: `AS-${Date.now().toString().slice(-7)}`,
        time: new Date().toLocaleString(),
        model_version: modelVersion,
        ...prediction,
      }, ...current])
      setNotice('Prediction completed successfully.')
    } catch (error) {
      setPredictionError(error.message || 'Prediction failed. Check the API and model status.')
    } finally {
      setBusy(false)
    }
  }

  function saveConnection(url) {
    const clean = url.trim().replace(/\/+$/, '')
    setConnectionUrl(clean)
    setApiUrl(clean)
    setNotice('API connection updated.')
  }

  return (
    <div className="app-shell">
      <Sidebar active={active} onNavigate={setActive} apiStatus={apiStatus} />
      <main className="main-area">
        <Topbar active={active} onRefresh={() => refreshStatus()} refreshing={refreshing} />
        <div className="page-content">
          {notice && <div className="success-notice"><Icon name="check" size={17} />{notice}<button onClick={() => setNotice('')} aria-label="Dismiss notification">×</button></div>}
          {active === 'overview' && <Overview health={health} modelInfo={modelInfo} assessments={assessments} apiStatus={apiStatus} onNavigate={setActive} />}
          {active === 'assessment' && <LoanAssessment onResult={runPrediction} busy={busy} result={result} error={predictionError} clearResult={() => { setResult(null); setPredictionError('') }} />}
          {active === 'history' && <HistoryPage assessments={assessments} onNavigate={setActive} />}
          {active === 'monitoring' && <MonitoringPage health={health} modelInfo={modelInfo} apiStatus={apiStatus} onRefresh={() => refreshStatus()} refreshing={refreshing} error={monitoringError} />}
          {active === 'settings' && <SettingsPage apiUrl={apiUrl} setApiUrl={setApiUrl} onSave={saveConnection} />}
          <footer className="app-footer"><span>RISKLENS <span className="footer-separator">·</span> LOAN DEFAULT MLOPS</span><span>Local model serving workspace</span></footer>
        </div>
      </main>
    </div>
  )
}

async function fetchJsonFrom(baseUrl, path, options = {}) {
  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  })

  const data = await response.json()

  if (!response.ok) {
    const message = typeof data.detail === 'string'
      ? data.detail
      : JSON.stringify(data.detail ?? data)

    throw new Error(message || `Request failed (${response.status})`)
  }

  return data
}
