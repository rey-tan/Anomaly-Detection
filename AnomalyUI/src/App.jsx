import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./App.css";
import { fetchProfile, analyze, fetchAnalyses, fetchAnalysisData, explainAnalysis } from "./api";
import AppRoutes from './routes/AppRoutes'

const STORAGE_KEY = "anomalyui_token";

// Helper function to extract metrics and params from new response format
function extractMetricsAndParams(data) {
  if (!data) return { metrics: {}, bestParams: {} };
  
  // If using new format with models
  if (data.models) {
    const metrics = {};
    const bestParams = {};
    Object.entries(data.models).forEach(([modelName, modelResult]) => {
      if (modelResult.metrics) metrics[modelName] = modelResult.metrics;
      if (modelResult.params) {
        const paramKey = modelName === 'zscore' ? 'z_score' : modelName;
        bestParams[paramKey] = modelResult.params;
      }
    });
    return { metrics, bestParams };
  }
  
  // Fallback to old format
  return {
    metrics: data.metrics || {},
    bestParams: data.best_params || {},
  };
}

function parseAiExplanationEntries(summary) {
  if (!summary) return [];
  const rowPattern = /^\*\*Row\s+(\d+):\s*([^*]+)\*\*/gm;
  const matches = Array.from(summary.matchAll(rowPattern));
  if (!matches.length) return [];

  return matches.map((match, index) => {
    const rowNumber = Number(match[1]);
    const date = match[2].trim();
    const start = match.index + match[0].length;
    const end = index + 1 < matches.length ? matches[index + 1].index : summary.length;
    const block = summary.slice(start, end).trim();
    const trimmed = block.split("**Overall Summary:**")[0].trim();
    const parts = trimmed.split("**Summary:**");
    const bulletsText = parts[0].trim();
    const rowSummary = parts[1] ? parts[1].trim() : "";
    const bullets = bulletsText
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter((line) => line.startsWith("-") || line.startsWith("*"))
      .map((line) => line.replace(/^[-*]\s*/, ""));

    return {
      rowNumber,
      date,
      bullets,
      summary: rowSummary,
    };
  });
}

function isAnomalyRow(row) {
  return (
    row.cluster === -1 ||
    row.anomaly === true ||
    row.cluster_dbscan === -1 ||
    row.cluster_isolation_forest === -1
  );
}



function App() {
  const [token, setToken] = useState(localStorage.getItem(STORAGE_KEY) || "");
  const [user, setUser] = useState(null);
  const [results, setResults] = useState(null);
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  const [lastConfig, setLastConfig] = useState(null);
  const [activityUser, setActivityUser] = useState(null);
  const [aiExplanation, setAiExplanation] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

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

  useEffect(() => {
    if (!token || lastConfig) return;

    let active = true;
    fetchAnalyses(token)
      .then((analyses) => {
        if (!active || !analyses?.length) return;
        setLastConfig(analyses[0]);
      })
      .catch(() => {});

    return () => {
      active = false;
    };
  }, [token, lastConfig]);

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
    setLastConfig(null);
    setAiExplanation(null);
    setAiLoading(false);
    setAiError("");
    setError("");
  };

  const handleAnalyze = async (payload) => {
    setError("");
    setLoading(true);
    try {
      const response = await analyze(token, payload);
      setResults(response);
      setLastConfig(payload);
      setAiExplanation(null);
      setAiError("");
      navigate('/results');
    } catch (err) {
      setError(err.message || "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const handleOpenLastRun = async (payload, analysis) => {
    setError("");
    try {
      if (payload && analysis) {
        setResults(payload);
        setSelectedAnalysis(analysis);
        setLastConfig(analysis);
        setAiExplanation(null);
        setAiError("");
        navigate('/results');
        return;
      }

      const analyses = await fetchAnalyses(token);
      const latest = analyses?.[0];

      if (!latest) {
        setError("No saved analyses found yet.");
        return;
      }

      const latestPayload = await fetchAnalysisData(token, latest.id);
      setResults(latestPayload);
      setSelectedAnalysis(latest);
      setLastConfig(latest);
      setAiExplanation(null);
      setAiError("");
      navigate('/results');
    } catch (err) {
      setError(err.message || "Could not open the latest analysis");
    }
  };

  const aiExplanationEntries = useMemo(() => {
    if (!aiExplanation) return [];
    if (Array.isArray(aiExplanation.entries) && aiExplanation.entries.length) {
      
      return aiExplanation.entries.map((entry) => ({
        rowNumber: entry.row_number || entry.rowNumber,
        date: entry.date,
        bullets: entry.bullets || [],
        summary: entry.summary,
      }));
    }
    return parseAiExplanationEntries(aiExplanation.summary || "");
  }, [aiExplanation]);

  const anomalyRows = useMemo(
    () =>
      (results?.data || []).filter(
        (item) =>
          item.cluster === -1 ||
          item.anomaly === true ||
          item.cluster_dbscan === -1 ||
          item.cluster_isolation_forest === -1
      ),
    [results]
  );

  const handleExplainWithAI = async () => {
    if (!results?.data?.length) return;
    setAiLoading(true);
    setAiError("");
    try {
      const contextualRows = anomalyRows.map((row) => {
        const index = results.data.findIndex((item) => item.date === row.date);
        const previousRows = index > 0 ? results.data.slice(Math.max(0, index - 3), index) : [];
        const nextRows = index < results.data.length - 1 ? results.data.slice(index + 1, index + 4) : [];
        const windowStart = Math.max(0, index - 20);
        const window = results.data.slice(windowStart, index);
        const averageVolume = window.length
          ? window.reduce((sum, item) => sum + (item.volume || 0), 0) / window.length
          : null;

        return {
          ...row,
          previous_close: previousRows.length ? previousRows[previousRows.length - 1].close : null,
          adjacent_rows: [...previousRows, ...nextRows].map((item) => ({
            date: item.date,
            close: item.close,
            volume: item.volume,
            change: item.change,
          })),
          rolling_mean: row.SMA_20 ?? row.SMA_10 ?? null,
          rolling_std: row.volatility ?? null,
          average_volume: averageVolume,
          detector_flags: [
            row.cluster === -1 ? "combined" : null,
            row.cluster_dbscan === -1 ? "DBSCAN" : null,
            row.cluster_isolation_forest === -1 ? "Isolation Forest" : null,
          ].filter(Boolean),
          z_score: row.z_score ?? row.Anomaly_Z_Score ?? null,
          bb_width: row.bb_width ?? row.BB_width ?? row.bbWidth ?? null,
          RSI: row.RSI ?? row.rsi ?? null,
          Upper_BB: row.Upper_BB ?? row.upper_bb ?? null,
          Lower_BB: row.Lower_BB ?? row.lower_bb ?? null,
          Anomaly_Score_IF: row.Anomaly_Score_IF ?? row.IF_Anomaly_Score ?? row.ifScore ?? null,
        };
      });

      const { metrics, bestParams } = extractMetricsAndParams(results);
      const selectedAnalysisParams = extractMetricsAndParams(selectedAnalysis);
      
      const payload = {
        stock: lastConfig?.stock || selectedAnalysis?.stock || "",
        mode: lastConfig?.mode || selectedAnalysis?.mode || "",
        timeframe: lastConfig?.timeframe || selectedAnalysis?.timeframe || "",
        start_date: lastConfig?.start_date || selectedAnalysis?.start_date || "",
        end_date: lastConfig?.end_date || selectedAnalysis?.end_date || "",
        metrics: metrics,
        best_params: bestParams || selectedAnalysisParams.bestParams || {},
        data: contextualRows,
      };
      const explanation = await explainAnalysis(token, payload);
      setAiExplanation(explanation);
    } catch (err) {
      setAiError(err.message || "Failed to generate AI explanation");
    } finally {
      setAiLoading(false);
    }
  };

  return (
    <AppRoutes
      user={user}
      token={token}
      results={results}
      selectedAnalysis={selectedAnalysis}
      setResults={setResults}
      setSelectedAnalysis={setSelectedAnalysis}
      aiExplanation={aiExplanation}
      aiExplanationEntries={aiExplanationEntries}
      aiError={aiError}
      aiLoading={aiLoading}
      handleExplainWithAI={handleExplainWithAI}
      activityUser={activityUser}
      handleOpenLastRun={handleOpenLastRun}
      handleAnalyze={handleAnalyze}
      loading={loading}
      error={error}
      lastConfig={lastConfig}
      onLogout={handleLogout}
      onOpenNotifications={() => navigate('/notifications')}
      setActivityUser={setActivityUser}
      handleLogin={handleLogin}
    />
  );
}

export default App;
