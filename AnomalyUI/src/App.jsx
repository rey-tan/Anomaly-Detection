import { useEffect, useMemo, useState } from "react";
import "./App.css";
import { login, fetchProfile, analyze } from "./api";
import AnalysisPanel from "./components/AnalysisPanel";
import AnomalyChart from "./components/AnomalyChart";
import MetricsGrid from "./components/MetricsGrid";
import SaveCacheButton from "./components/SaveCacheButton";

const STORAGE_KEY = "anomalyui_token";

function Header({ user, onLogout }) {
  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">Anomaly Engine</p>
        <h1>Detect hidden market risk with precision.</h1>
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
      <div className="auth-panel">
        <div className="brand-block">
          <p className="eyebrow">Secure access</p>
          <h1>Sign in to Anomaly Engine</h1>
          <p>Use your analyst account to run real-time anomaly detection and review actionable findings.</p>
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

function ResultStats({ data = [], metrics = {} }) {
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

function App() {
  const [token, setToken] = useState(localStorage.getItem(STORAGE_KEY) || "");
  const [user, setUser] = useState(null);
  const [results, setResults] = useState(null);
  const [lastConfig, setLastConfig] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showUsers, setShowUsers] = useState(false);

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
    } catch (err) {
      setError(err.message || "Unable to load profile");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem(STORAGE_KEY);
    setToken("");
    setUser(null);
    setResults(null);
    setError("");
  };

  const handleAnalyze = async (payload) => {
    setError("");
    setLoading(true);
    try {
      const response = await analyze(token, payload);
      setResults(response);
      setLastConfig(payload);
    } catch (err) {
      setError(err.message || "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const summary = useMemo(() => {
    if (!results) return null;
    return {
      metrics: results.metrics,
      bestParams: results.best_params,
      data: results.data,
    };
  }, [results]);

  if (!token) {
    return <LoginPage onSuccess={handleLogin} />;
  }

  return (
    <div className="app-shell">
      <Header user={user} onLogout={handleLogout} />

      <div style={{ display: "flex", gap: 12, marginBottom: 12 }}>
        {user?.role === "admin" ? (
          <button className="primary-button" onClick={() => setShowUsers((s) => !s)}>{showUsers ? "Close users" : "Manage users"}</button>
        ) : null}
        {results ? <span style={{ alignSelf: "center", color: "#94a3b8" }}>Last run: {lastConfig?.stock || "—"} </span> : null}
      </div>

      <main className="content-grid">
        <div className="left-panel">
          <AnalysisPanel onSubmit={handleAnalyze} loading={loading} />
          {error ? <div className="alert-box">{error}</div> : null}
          {results ? <ResultStats data={results.data || []} metrics={results.metrics} /> : null}
          {results && lastConfig ? (
            <div style={{ marginTop: 12 }}>
              <SaveCacheButton token={token} config={lastConfig} results={results} onSaved={() => {}} />
            </div>
          ) : null}
          {showUsers && user?.role === "admin" ? <UsersPanel token={token} /> : null}
        </div>

        <div className="right-panel">
          <section className="hero-card">
            <div>
              <p className="eyebrow">Live insights</p>
              <h2>Fast review of your last analysis</h2>
              <p>Visualize anomalies, model health, and the latest tuning parameters in one view.</p>
            </div>
            <div className="hero-footer">
              <span>{user?.role ? `Role: ${user.role}` : "Analyst dashboard"}</span>
              <strong>Backend API: {import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"}</strong>
            </div>
          </section>

          {results ? (
            <>
              <MetricsGrid metrics={results.metrics} bestParams={results.best_params} />
              <AnomalyChart data={results.data || []} />
            </>
          ) : (
            <section className="empty-state-card">
              <h2>Begin your first run</h2>
              <p>Complete the form on the left and submit an analysis configuration to unlock charts and anomaly details.</p>
            </section>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
