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

function countAnomalyRows(data) {
  if (!Array.isArray(data)) return 0;
  return data.filter(isAnomalyRow).length;
}

function deriveAnomalyCount(metrics, dataLength = 0) {
  if (!metrics || typeof metrics !== 'object') return null;
  if (typeof metrics.anomaly_count === 'number') {
    return metrics.anomaly_count;
  }
  if (typeof metrics.n_noise === 'number') {
    return metrics.n_noise;
  }
  if (typeof metrics.anomaly_rate === 'number' && dataLength > 0) {
    return Math.round(metrics.anomaly_rate * dataLength);
  }
  return null;
}

async function enrichAnalysisWithAnomalyCount(analysis, token, fallbackData = null) {
  if (!analysis) return analysis;
  let anomalyCount = null;
  if (Array.isArray(fallbackData)) {
    anomalyCount = countAnomalyRows(fallbackData);
  }
  if (anomalyCount === null) {
    anomalyCount = deriveAnomalyCount(analysis.metrics, Array.isArray(analysis.data) ? analysis.data.length : 0);
  }
  if (anomalyCount === null && analysis.id && token) {
    try {
      const payload = await fetchAnalysisData(token, analysis.id);
      anomalyCount = countAnomalyRows(payload.data || []);
    } catch (err) {
      anomalyCount = 0;
    }
  }
  return { ...analysis, anomalyCount: anomalyCount ?? 0 };
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
  const [analyses, setAnalyses] = useState([]);
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
    if (!token) return;
    let active = true;
    (async () => {
      try {
        const list = await fetchAnalyses(token).catch(() => []);
        if (!active) return;
        setAnalyses(list || []);
        if (!selectedAnalysis && list?.length) {
          const latest = list[0];
          const enriched = await enrichAnalysisWithAnomalyCount(latest, token);
          if (!active) return;
          setSelectedAnalysis(enriched);
        }
      } catch (err) {
        // ignore errors on initial history load
      }
    })();

    return () => {
      active = false;
    };
  }, [token, selectedAnalysis]);

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
    setSelectedAnalysis(null);
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
      const currentAnomalyCount = countAnomalyRows(response.data || []);
      let selected = { ...payload, anomalyCount: currentAnomalyCount };
      try {
        const analyses = await fetchAnalyses(token);
        if (analyses?.length) {
          selected = await enrichAnalysisWithAnomalyCount(analyses[0], token, response.data);
        }
      } catch (err) {
        // If the history lookup fails, keep using the request payload as a fallback.
      }
      setSelectedAnalysis(selected);
      setAiExplanation(null);
      setAiError("");
      try {
        window.dispatchEvent(new CustomEvent('notificationsUpdated'));
      } catch (e) {
        // ignore if browser does not support CustomEvent in this environment
      }
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
        const enriched = analysis.anomalyCount != null ? analysis : { ...analysis, anomalyCount: countAnomalyRows(payload.data || []) };
        setResults(payload);
        setSelectedAnalysis(enriched);
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
      setAiExplanation(null);
      setAiError("");
      navigate('/results');
    } catch (err) {
      setError(err.message || "Could not open the latest analysis");
    }
  };

  const handleSelectAnalysis = async (analysisId) => {
    if (!token || !analysisId) return;
    setError("");
    try {
      const payload = await fetchAnalysisData(token, analysisId);
      let analysis = analyses.find((item) => item.id === analysisId);
      if (!analysis) {
        const list = await fetchAnalyses(token);
        setAnalyses(list || []);
        analysis = list?.find((item) => item.id === analysisId);
      }
      const enriched = analysis
        ? await enrichAnalysisWithAnomalyCount(analysis, token, payload.data)
        : { id: analysisId, anomalyCount: countAnomalyRows(payload.data || []), ...payload };
      setResults(payload);
      setSelectedAnalysis(enriched);
      setAiExplanation(null);
      setAiError("");
      navigate('/results');
    } catch (err) {
      setError(err.message || "Failed to load historical analysis");
      throw err;
    }
  };

  const aiExplanationMarkdown = useMemo(() => {
    if (!aiExplanation) return "";
    return aiExplanation.raw_summary || aiExplanation.summary || "";
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
        stock: selectedAnalysis?.stock || "",
        mode: selectedAnalysis?.mode || "",
        timeframe: selectedAnalysis?.timeframe || "",
        start_date: selectedAnalysis?.start_date || "",
        end_date: selectedAnalysis?.end_date || "",
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
      analyses={analyses}
      setAnalyses={setAnalyses}
      results={results}
      selectedAnalysis={selectedAnalysis}
      setResults={setResults}
      setSelectedAnalysis={setSelectedAnalysis}
      aiExplanation={aiExplanation}
      aiExplanationMarkdown={aiExplanationMarkdown}
      aiError={aiError}
      aiLoading={aiLoading}
      handleExplainWithAI={handleExplainWithAI}
      activityUser={activityUser}
      handleOpenLastRun={handleOpenLastRun}
      handleAnalyze={handleAnalyze}
      handleSelectAnalysis={handleSelectAnalysis}
      loading={loading}
      error={error}
      onLogout={handleLogout}
      onOpenNotifications={() => navigate('/notifications')}
      setActivityUser={setActivityUser}
      handleLogin={handleLogin}
    />
  );
}

export default App;
