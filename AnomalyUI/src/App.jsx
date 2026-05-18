import { useEffect, useMemo, useState } from "react";
import "./App.css";
import { login, fetchProfile, analyze, toggleFavorite } from "./api";
import AnalysisPanel from "./components/AnalysisPanel";
import AnomalyChart from "./components/AnomalyChart";
import MetricsGrid from "./components/MetricsGrid";
import UsersPanel from "./components/UsersPanel";
import AnalysisHistory from "./components/AnalysisHistory";

const STORAGE_KEY = "anomalyui_token";
const DEFAULT_PAGE = "dashboard";

const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", description: "Overview" },
  { id: "analysis", label: "Analysis", description: "Run model" },
  { id: "results", label: "Results", description: "Charts & metrics" },
  { id: "users", label: "Users", description: "Admin only" },
];

function Header({ user, onLogout }) {
  return (
    <header className="topbar">
      <div className="topbar-copy">
        <p className="eyebrow">Anomaly Engine</p>
        <h1>Detect hidden market risk with precision.</h1>
        <p className="topbar-subtitle">
          Separate pages for navigation, analysis, results, and admin tools. The workspace stays focused instead of stacking everything in one screen.
        </p>
      </div>
      <div className="user-chip">
        <div>
          <span>Signed in as</span>
          <strong>{user?.username || "Guest"}</strong>
        </div>
        <button className="text-button" onClick={onLogout}>
          Sign out
        </button>
      </div>
    </header>
  );
}

function LoginPage({ onSuccess }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const response = await login(username, password);
      onSuccess(response.access_token);
    } catch (err) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-page">
      <div className="auth-background">
        <span />
        <span />
        <span />
      </div>
      <div className="auth-panel">
        <div className="brand-block">
          <p className="eyebrow">Secure access</p>
          <h1>Sign in to Anomaly Engine</h1>
          <p>Use your analyst account to run anomaly detection, review findings, and manage the workspace in dedicated pages.</p>
        </div>
        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            Username
            <input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              autoComplete="username"
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              required
            />
          </label>
          <button type="submit" className="primary-button" disabled={loading}>
            {loading ? "Authenticating…" : "Sign in"}
          </button>
          {error ? <div className="form-error">{error}</div> : null}
        </form>
      </div>
    </main>
  );
}

function ResultStats({ data = [] }) {
  const anomalyCount = data.filter((item) => item.cluster === -1).length;
  const points = data.length;
  const firstDate = data[0]?.date || data[0]?.transaction_time || "—";
  const lastDate = data[data.length - 1]?.date || data[data.length - 1]?.transaction_time || "—";

  return (
    <div className="result-summary">
      <div className="summary-card">
        <span>Data points</span>
        <strong>{points}</strong>
      </div>
      <div className="summary-card">
        <span>Anomalies flagged</span>
        <strong>{anomalyCount}</strong>
      </div>
      <div className="summary-card">
        <span>Analysis window</span>
        <strong>
          {firstDate} → {lastDate}
        </strong>
      </div>
    </div>
  );
}

function NavButton({ item, active, onClick, badge }) {
  return (
    <button className={active ? "nav-item active" : "nav-item"} onClick={onClick} type="button">
      <span className="nav-item-label">
        <strong>{item.label}</strong>
        <small>{item.description}</small>
      </span>
      {badge ? <span className="nav-badge">{badge}</span> : null}
    </button>
  );
}

function StatCard({ label, value, helper }) {
  return (
    <article className="stat-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {helper ? <p>{helper}</p> : null}
    </article>
  );
}

function App() {
  const [token, setToken] = useState(localStorage.getItem(STORAGE_KEY) || "");
  const [user, setUser] = useState(null);
  const [results, setResults] = useState(null);
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  const [lastConfig, setLastConfig] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [page, setPage] = useState(DEFAULT_PAGE);

  useEffect(() => {
    if (!token) return;

    fetchProfile(token)
      .then((profile) => setUser(profile))
      .catch(() => {
        localStorage.removeItem(STORAGE_KEY);
        setToken("");
        setUser(null);
      });
  }, [token]);

  const handleLogin = async (accessToken) => {
    localStorage.setItem(STORAGE_KEY, accessToken);
    setToken(accessToken);
    try {
      const profile = await fetchProfile(accessToken);
      setUser(profile);
      setPage(DEFAULT_PAGE);
    } catch (err) {
      setError(err.message || "Unable to load profile");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem(STORAGE_KEY);
    setToken("");
    setUser(null);
    setResults(null);
    setLastConfig(null);
    setError("");
    setPage(DEFAULT_PAGE);
  };

  const handleAnalyze = async (payload) => {
    setError("");
    setLoading(true);
    try {
      const response = await analyze(token, payload);
      setResults(response);
      setLastConfig(payload);
      setPage("results");
    } catch (err) {
      setError(err.message || "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const anomalyCount = useMemo(() => results?.data?.filter((item) => item.cluster === -1).length || 0, [results]);
  const activeMetricCount = useMemo(() => Object.keys(results?.metrics || {}).length, [results]);
  const navItems = useMemo(() => {
    return NAV_ITEMS.filter((item) => item.id !== "users" || user?.role === "admin");
  }, [user]);

  if (!token) {
    return <LoginPage onSuccess={handleLogin} />;
  }

  return (
    <div className="app-shell">
      <Header user={user} onLogout={handleLogout} />
      <section className="workspace-grid">
        <aside className="side-rail">
          <div className="side-rail-card">
            <p className="eyebrow">Workspace</p>
            <h2>Pages</h2>
            <p>Jump between focused views instead of scrolling through one long page.</p>
          </div>
          <nav className="nav-stack" aria-label="Primary">
            {navItems.map((item) => (
              <NavButton
                key={item.id}
                item={item}
                active={page === item.id}
                onClick={() => setPage(item.id)}
                badge={item.id === "results" && results ? "Live" : null}
              />
            ))}
          </nav>

          <div className="side-rail-card side-rail-footer">
            <span>Last run</span>
            <strong>{lastConfig?.stock || "No analysis yet"}</strong>
            <p>{lastConfig ? `${lastConfig.timeframe} • ${lastConfig.mode}` : "Run an analysis to populate charts and metrics."}</p>
          </div>
        </aside>

        <main className="page-stage">
          {page === "dashboard" ? (
            <>
              <section className="hero-card hero-card-split">
                <div>
                  <p className="eyebrow">Live insights</p>
                  <h2>Overview of the current anomaly workspace</h2>
                  <p>Track model health, see the last analyzed symbol, and move into a dedicated page for the next task.</p>
                </div>
                <div className="hero-footer">
                  <span>{user?.role ? `Role: ${user.role}` : "Analyst dashboard"}</span>
                  <strong>Backend API: {import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"}</strong>
                </div>
              </section>

              <section className="stats-grid">
                <StatCard label="Current page" value="Dashboard" helper="Use the sidebar to switch to analysis, results, or admin pages." />
                <StatCard label="Latest symbol" value={lastConfig?.stock || "—"} helper="Most recent analysis target." />
                <StatCard label="Flagged anomalies" value={anomalyCount} helper="Count from the latest result set." />
                <StatCard label="Metrics groups" value={activeMetricCount} helper="How many models are currently summarized." />
              </section>

              <section className="dashboard-grid">
                <article className="dashboard-card">
                  <div className="section-heading compact">
                    <div>
                      <h2>Quick actions</h2>
                      <p>Open a focused page for the task you want to complete next.</p>
                    </div>
                  </div>
                  <div className="quick-links">
                    <button className="quick-link" onClick={() => setPage("analysis")} type="button">
                      Run a new analysis
                    </button>
                    <button className="quick-link" onClick={() => setPage("results")} type="button" disabled={!results}>
                      Review latest results
                    </button>
                    {user?.role === "admin" ? (
                      <button className="quick-link" onClick={() => setPage("users")} type="button">
                        Manage users
                      </button>
                    ) : null}
                  </div>
                </article>

                <article className="dashboard-card">
                  <div className="section-heading compact">
                    <div>
                      <h2>Analysis context</h2>
                      <p>The most recent configuration is kept separate from the charts page so it does not clutter the layout.</p>
                    </div>
                  </div>
                  <div className="context-stack">
                    <div className="context-row">
                      <span>Mode</span>
                      <strong>{lastConfig?.mode || "—"}</strong>
                    </div>
                    <div className="context-row">
                      <span>Timeframe</span>
                      <strong>{lastConfig?.timeframe || "—"}</strong>
                    </div>
                    <div className="context-row">
                      <span>Feature count</span>
                      <strong>{lastConfig?.features?.length || 0}</strong>
                    </div>
                  </div>
                </article>
              </section>
            </>
          ) : null}

          {page === "analysis" ? (
            <section className="page-split">
              <div className="page-panel">
                <div className="page-intro">
                  <p className="eyebrow">Analysis page</p>
                  <h2>Run a new anomaly detection job</h2>
                  <p>Use one focused page for configuration and submission so the analysis form does not compete with the results view.</p>
                </div>
                <AnalysisPanel onSubmit={handleAnalyze} loading={loading} />
                {error ? <div className="alert-box">{error}</div> : null}
              </div>

              <aside className="page-panel page-panel-aside">
                <div className="page-intro compact-copy">
                  <p className="eyebrow">Before you run</p>
                  <h3>Keep the set small and intentional</h3>
                  <p>Choose the symbol, window, and features you actually want to inspect. You can move to the results page after the run completes.</p>
                </div>
                <div className="context-stack">
                  <div className="context-row">
                    <span>Selected page</span>
                    <strong>Analysis</strong>
                  </div>
                  <div className="context-row">
                    <span>Saved cache</span>
                    <strong>{results && lastConfig ? "Available" : "Not yet"}</strong>
                  </div>
                </div>
                {null}
              </aside>
            </section>
          ) : null}

          {page === "results" ? (
            <section className="page-split results-layout">
              <div className="page-panel">
                <div className="page-intro">
                  <p className="eyebrow">Results page</p>
                  <h2>Inspect the latest analysis outputs</h2>
                  <p>The chart, metrics, and tuned parameters are now isolated here instead of sitting on the same page as the input form.</p>
                  {selectedAnalysis ? (
                    <div className="favorite-row">
                      <button
                        className="favorite-button large"
                        onClick={async () => {
                          try {
                            const updated = await toggleFavorite(token, selectedAnalysis.id, !selectedAnalysis.is_favorite);
                            setSelectedAnalysis(updated);
                          } catch (err) {
                            console.error(err);
                          }
                        }}
                      >
                        {selectedAnalysis.is_favorite ? "★ Favorite" : "☆ Save to favorites"}
                      </button>
                    </div>
                  ) : null}
                </div>
                {results ? <ResultStats data={results.data || []} metrics={results.metrics} /> : null}
                {results ? <MetricsGrid metrics={results.metrics} bestParams={results.best_params} /> : <section className="empty-state-card"><h2>No results yet</h2><p>Run an analysis from the Analysis page to populate this view.</p></section>}
              </div>

              <div className="page-panel">
                {results ? <AnomalyChart data={results.data || []} /> : <section className="empty-state-card"><h2>Chart preview</h2><p>Once analysis is complete, price action and anomaly markers appear here.</p></section>}
                {null}
              </div>

              <aside className="page-panel">
                <AnalysisHistory token={token} onSelect={(payload, analysis) => { setResults(payload); setSelectedAnalysis(analysis); setPage('results'); }} />
              </aside>
            </section>
          ) : null}

          {page === "users" && user?.role === "admin" ? (
            <section className="page-split single-column">
              <div className="page-panel">
                <div className="page-intro">
                  <p className="eyebrow">Admin page</p>
                  <h2>Manage users separately from analysis work</h2>
                  <p>Keeping the admin tools on their own page makes the analyst workflow cleaner.</p>
                </div>
                <UsersPanel token={token} />
              </div>
            </section>
          ) : null}

          {page === "users" && user?.role !== "admin" ? (
            <section className="empty-state-card">
              <h2>Admin access required</h2>
              <p>Only admin users can open the user management page.</p>
            </section>
          ) : null}
        </main>
      </section>
    </div>
  );
}

export default App;
