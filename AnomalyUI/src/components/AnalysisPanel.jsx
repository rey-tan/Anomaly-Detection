import React from "react";
import { useEffect, useMemo, useState } from "react";
import { analyze,fetchSymbols} from "../api";
import { useNavigate } from "react-router-dom";
import {  countAnomalyRows,  enrichAnalysisWithAnomalyCount } from '../utils/analysisHelpers';



const today = new Date();
const defaultStart = new Date(today);
defaultStart.setDate(defaultStart.getDate() - 365);

const endDate = today.toISOString().split('T')[0];
const startDate = defaultStart.toISOString().split('T')[0];

export default function AnalysisPanel({ token,setError,setResults,setSelectedAnalysis}) {
  const [symbols, setSymbols] = useState([]);
  const [symbolsLoading, setSymbolsLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();


  
  const [form, setForm] = useState({
    stock: "API",
    timeframe: "1D",
    start_date: startDate,
    end_date: endDate,
  });
  const onSubmit = async (payload) => {
      setError("");
      setLoading(true);
      try {
        const response = await analyze(token, payload);
        setResults(response);
        console.log(response);
        const currentAnomalyCount = countAnomalyRows(response.data || []);
        let selected = { ...payload, anomalyCount: currentAnomalyCount,analysis_id: response.analysis_id };
        try {
          const analyses = await fetchAnalyses(token);
          if (analyses?.length) {
            selected = await enrichAnalysisWithAnomalyCount(analyses[0], token, response.data);
          }
        } catch (err) {
          // If the history lookup fails, keep using the request payload as a fallback.
        }
        setSelectedAnalysis(selected);
        
        
        navigate('/results');
      } catch (err) {
        setError(err.message || "Analysis failed");
      } finally {
        setLoading(false);
      }
    };

  useEffect(() => {
    let active = true;

    async function loadSymbols() {
      try {
        const availableSymbols = await fetchSymbols(token);
        if (!active) return;

        const normalized = Array.isArray(availableSymbols) ? availableSymbols : [];
        setSymbols(normalized);
        setForm((prev) => ({
          ...prev,
          stock: prev.stock || normalized[0] || "",
        }));
      } catch {
        if (!active) return;
        console.log("Failed to load symbols, defaulting to API");
        setSymbols(["API"]);
        setForm((prev) => ({
          ...prev,
          stock: prev.stock || "API",
        }));
      } finally {
        if (active) {
          setSymbolsLoading(false);
        }
      }
    }

    loadSymbols();

    return () => {
      active = false;
    };
  }, []);

  const canSubmit = useMemo(() => {
    const start = new Date(form.start_date);
    const end = new Date(form.end_date);
    return form.stock.trim() && form.start_date && form.end_date && start <= end;
  }, [form]);

  

  return (
    <form
      className="panel-card"
      onSubmit={(event) => {
        event.preventDefault();
        if (!canSubmit) return;
        onSubmit(form);
      }}
    >
      <div className="section-heading">
        <div>
          <h3>Run anomaly analysis</h3>
          <p>Choose the dataset and time range to uncover outlier events.</p>
        </div>
      </div>

      <div className="field-grid">
        <label className="field-group">
          <span>Symbol</span>
          <select
            value={form.stock}
            onChange={(event) => setForm((prev) => ({ ...prev, stock: event.target.value }))}
            disabled={symbolsLoading && symbols.length === 0}
          >
            {symbolsLoading && symbols.length === 0 ? <option value="">Loading symbols...</option> : null}
            {symbols.map((symbol) => (
              <option key={symbol} value={symbol}>
                {symbol}
              </option>
            ))}
          </select>
        </label>
       
        <label className="field-group">
          <span>Timeframe</span>
          <select
            value={form.timeframe}
            onChange={(event) => setForm((prev) => ({ ...prev, timeframe: event.target.value }))}
          >
            <option value="1D">1 day</option>
          </select>
        </label>
      </div>

      <div className="field-grid">
        <label className="field-group">
          <span>Start date</span>
          <input
            type="date"
            value={form.start_date}
            onChange={(event) => setForm((prev) => ({ ...prev, start_date: event.target.value }))}
          />
        </label>
        <label className="field-group">
          <span>End date</span>
          <input
            type="date"
            value={form.end_date}
            onChange={(event) => setForm((prev) => ({ ...prev, end_date: event.target.value }))}
          />
        </label>
      </div>

      

      <div className="form-footer">
        <button type="submit" className="primary-button" disabled={!canSubmit || loading}>
          {loading ? "Analyzing..." : "Run analysis"}
        </button>
      </div>
    </form>
  );
}
