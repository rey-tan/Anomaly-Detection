import { useEffect, useMemo, useState } from "react";
import { fetchSymbols } from "../api";

const defaultFeatures = [
  "close",
  "volume",
  "volatility",
  "returns",
  "RSI",
  "SMA_10",
  "SMA_20",
  "SMA_50",
];

export default function AnalysisPanel({ onSubmit, loading }) {
  const [symbols, setSymbols] = useState([]);
  const [symbolsLoading, setSymbolsLoading] = useState(true);
  const [form, setForm] = useState({
    stock: "",
    timeframe: "1D",
    mode: "Static",
    start_date: "2026-01-01",
    end_date: "2026-01-31",
    features: ["bb_width", "volume", "volatility", "returns"],
  });

  useEffect(() => {
    let active = true;

    async function loadSymbols() {
      try {
        const availableSymbols = await fetchSymbols();
        if (!active) return;

        const normalized = Array.isArray(availableSymbols) ? availableSymbols : [];
        setSymbols(normalized);
        setForm((prev) => ({
          ...prev,
          stock: prev.stock || normalized[0] || "",
        }));
      } catch {
        if (!active) return;
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
    return form.stock.trim() && form.start_date && form.end_date && form.features.length > 0;
  }, [form]);

  const toggleFeature = (feature) => {
    setForm((prev) => {
      const nextFeatures = prev.features.includes(feature)
        ? prev.features.filter((item) => item !== feature)
        : [...prev.features, feature];
      return { ...prev, features: nextFeatures };
    });
  };

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
          <h2>Run anomaly analysis</h2>
          <p>Choose the dataset, mode, timeframe, and features to uncover outlier events.</p>
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
          <span>Mode</span>
          <select
            value={form.mode}
            onChange={(event) => setForm((prev) => ({ ...prev, mode: event.target.value }))}
          >
            <option value="Static">Static</option>
            <option value="Realtime">Realtime</option>
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

      {/* <div className="feature-panel">
        <div className="feature-heading">
          <span>Feature selection</span>
          <p>Active features power the anomaly model.</p>
        </div>
        <div className="feature-grid">
          {defaultFeatures.map((feature) => (
            <button
              type="button"
              key={feature}
              className={form.features.includes(feature) ? "feature-pill active" : "feature-pill"}
              onClick={() => toggleFeature(feature)}
            >
              {feature}
            </button>
          ))}
        </div>
      </div> */}

      <div className="form-footer">
        <button type="submit" className="primary-button" disabled={!canSubmit || loading}>
          {loading ? "Analyzing..." : "Run analysis"}
        </button>
      </div>
    </form>
  );
}
