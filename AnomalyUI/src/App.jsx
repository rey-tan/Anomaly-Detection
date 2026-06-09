import React from 'react';
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./App.css";
import { fetchProfile, analyze, fetchAnalyses, fetchAnalysisData, explainAnalysis } from "./api";
import AppRoutes from './routes/AppRoutes'
import {  countAnomalyRows,  deriveAnomalyCount,  enrichAnalysisWithAnomalyCount } from './utils/analysisHelpers';

const STORAGE_KEY = "anomalyui_token";

function App() {
  const [token, setToken] = useState(localStorage.getItem(STORAGE_KEY) || "");
  const [user, setUser] = useState(null);
  const [results, setResults] = useState(null);
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  const [analyses, setAnalyses] = useState([]);
  const [activityUser, setActivityUser] = useState(null);
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
      console.log(err.message || "Unable to load profile");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem(STORAGE_KEY);
    setToken("");
    setUser(null);
    setResults(null);
    setSelectedAnalysis(null);
    
  };



  const handleOpenLastRun = async (payload, analysis) => {
    try {
      if (payload && analysis) {
        const enriched = analysis.anomalyCount != null ? analysis : { ...analysis, anomalyCount: countAnomalyRows(payload.data || []) };
        setResults(payload);
        setSelectedAnalysis(enriched);
        
        navigate('/results');
        return;
      }

      const analyses = await fetchAnalyses(token);
      const latest = analyses?.[0];

      if (!latest) {
        console.log("No saved analyses found yet.");
        return;
      }

      const latestPayload = await fetchAnalysisData(token, latest.id);
      setResults(latestPayload);
      setSelectedAnalysis(latest);
      
      navigate('/results');
    } catch (err) {
      console.log(err.message || "Could not open the latest analysis");
    }
  };

  const handleSelectAnalysis = async (analysisId) => {
    if (!token || !analysisId) return;
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
      navigate('/results');
    } catch (err) {
      console.log(err.message || "Failed to load historical analysis");
      throw err;
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
      activityUser={activityUser}
      handleOpenLastRun={handleOpenLastRun}
      handleSelectAnalysis={handleSelectAnalysis}
      onLogout={handleLogout}
      setActivityUser={setActivityUser}
      handleLogin={handleLogin}
    />
  );
}

export default App;
