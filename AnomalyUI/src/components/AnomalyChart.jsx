import { useEffect, useMemo, useRef, useState } from "react";
import { Line, Scatter } from "react-chartjs-2";
import {
  BarElement,
  Chart as ChartJS,
  CategoryScale,
  Filler,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  ScatterController,
  Tooltip,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ScatterController,
  Tooltip,
  Legend,
  Filler,
);

function getValue(row) {
  return row.close ?? row.price ?? row.adj_close ?? null;
}

function getLabel(row) {
  return row.date || row.transaction_time || "";
}

function getAnomalyState(row) {
  const dbscan = row.Anomaly_DBSCAN ?? row.cluster_dbscan ?? row.cluster;
  const isolationForest = row.Anomaly_Isolation_Forest ?? row.cluster_isolation_forest;

  return {
    dbscan,
    isolationForest,
    isAnomaly: dbscan === -1 || isolationForest === -1 || row.cluster === -1 || row.anomaly === true,
  };
}

function getAnomalyZScore(row, value, mean, stdDev) {
  const raw = row.Anomaly_Z_Score ?? row.z_score ?? row.Z_Score;
  if (raw != null && Number.isFinite(Number(raw))) return Number(raw);
  if (!Number.isFinite(value) || !Number.isFinite(stdDev) || stdDev === 0) return null;
  return (value - mean) / stdDev;
}

function chartOptions(yCallback, xLabels = []) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "nearest", intersect: false },
    plugins: {
      legend: {
        position: "top",
        labels: { color: "#eef2ff", boxWidth: 12, boxHeight: 12 },
      },
      tooltip: {
        backgroundColor: "rgba(15, 23, 42, 0.96)",
        titleColor: "#f8fafc",
        bodyColor: "#e2e8f0",
        borderColor: "rgba(148, 163, 184, 0.24)",
        borderWidth: 1,
      },
    },
    scales: {
      x: {
        title: { display: true, text: "Date", color: "#cbd5e1" },
        ticks: {
          color: "#cbd5e1",
          maxRotation: 0,
          autoSkip: true,
          maxTicksLimit: 8,
          display: true,
          callback: (value) => {
            const index = Number(value);
            if (index >= 0 && index < xLabels.length) {
              const label = String(xLabels[index]);
              return label.split("T")[0];
            }
            return value;
          },
        },
        grid: { display: false },
      },
      y: {
        ticks: { color: "#cbd5e1", callback: yCallback },
        grid: { color: "rgba(148, 163, 184, 0.14)" },
      },
    },
  };
}

function getDetectorLabel(state) {
  if (state.dbscan === -1 && state.isolationForest === -1) return "IF + DBSCAN";
  if (state.dbscan === -1) return "DBSCAN";
  if (state.isolationForest === -1) return "Isolation Forest";
  return "Model signal";
}

function useFullscreenFrame() {
  const frameRef = useRef(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    const onChange = () => setIsFullscreen(document.fullscreenElement === frameRef.current);
    document.addEventListener("fullscreenchange", onChange);
    return () => document.removeEventListener("fullscreenchange", onChange);
  }, []);

  const toggleFullscreen = async () => {
    if (!frameRef.current) return;
    if (document.fullscreenElement === frameRef.current) {
      await document.exitFullscreen();
      return;
    }
    await frameRef.current.requestFullscreen();
  };

  return { frameRef, isFullscreen, toggleFullscreen };
}

function ChartShell({ eyebrow, title, description, actionLabel, onAction, isFullscreen, frameRef, frameClassName = "", meta, children }) {
  return (
    <section className="chart-panel">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h3>{title}</h3>
          <p>{description}</p>
        </div>
        {onAction ? (
          <button type="button" className="fullscreen-button" onClick={onAction}>
            {isFullscreen ? `Exit ${actionLabel}` : actionLabel}
          </button>
        ) : null}
      </div>
      {meta}
      <div ref={frameRef} className={`chart-frame compact-chart fullscreen-target ${frameClassName} ${isFullscreen ? "is-fullscreen" : ""}`}>
        {children}
      </div>
    </section>
  );
}

function TechnicalChart({ data }) {
  const { frameRef, isFullscreen, toggleFullscreen } = useFullscreenFrame();
  const labels = data.map(getLabel);
  const closeSeries = data.map(getValue);
  const sma10 = data.map((row) => row.SMA_10 ?? null);
  const sma20 = data.map((row) => row.SMA_20 ?? null);
  const sma50 = data.map((row) => row.SMA_50 ?? null);
  const upperBB = data.map((row) => row.Upper_BB ?? null);
  const lowerBB = data.map((row) => row.Lower_BB ?? null);

  const chartData = {
    labels,
    datasets: [
      { label: "Close Price", data: closeSeries, borderColor: "#57c7ff", backgroundColor: "rgba(87, 199, 255, 0.14)", fill: true, tension: 0.25, pointRadius: 0, borderWidth: 2 },
      { label: "SMA 10", data: sma10, borderColor: "#fcbf49", borderDash: [6, 4], pointRadius: 0, tension: 0.2 },
      { label: "SMA 20", data: sma20, borderColor: "#8be9fd", borderDash: [6, 4], pointRadius: 0, tension: 0.2 },
      { label: "SMA 50", data: sma50, borderColor: "#a855f7", borderDash: [10, 6], pointRadius: 0, tension: 0.2 },
      { label: "Upper BB", data: upperBB, borderColor: "#f97316", borderDash: [4, 2], pointRadius: 0, tension: 0.2 },
      { label: "Lower BB", data: lowerBB, borderColor: "#f97316", borderDash: [4, 2], pointRadius: 0, tension: 0.2 },
    ].filter((dataset) => dataset.data.some((value) => value !== null && value !== undefined)),
  };

  return (
    <ChartShell
      eyebrow="1. Technical reference"
      title="Price, moving averages, and baseline context"
      description="Use this first chart to establish the technical reference before interpreting density or anomaly flags."
      actionLabel="Fullscreen"
      onAction={toggleFullscreen}
      isFullscreen={isFullscreen}
      frameRef={frameRef}
    >
      <div className="chart-inner">
        <Line data={chartData} options={chartOptions((value) => `Rs.${value}`, labels)} />
      </div>
    </ChartShell>
  );
}

function DensityChart({ data }) {
  const { frameRef, isFullscreen, toggleFullscreen } = useFullscreenFrame();
  const rows = data.filter((row) => Number.isFinite(Number(row.close ?? row.price)) && Number.isFinite(Number(row.volume)));
  const anomalyCount = data.filter((row) => getAnomalyState(row).isAnomaly).length;
  const scatterPoints = useMemo(() => {
    if (!rows.length) return [];

    const points = rows.map((row) => {
      const x = Number(row.close ?? row.price);
      const y = Number(row.volume);
      const state = getAnomalyState(row);
      const value = Number(getValue(row));

      return {
        x,
        y,
        anomaly: state.isAnomaly,
        dbscan: state.dbscan,
        isolationForest: state.isolationForest,
        label: getLabel(row),
        rawValue: value,
      };
    });

    const validPoints = points.filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y));
    if (!validPoints.length) return [];

    const bins = 18;
    const xs = validPoints.map((point) => point.x);
    const ys = validPoints.map((point) => point.y);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    const xStep = (maxX - minX || 1) / bins;
    const yStep = (maxY - minY || 1) / bins;
    const densityMap = new Map();

    validPoints.forEach((point) => {
      const xIndex = Math.max(0, Math.min(bins - 1, Math.floor((point.x - minX) / xStep)));
      const yIndex = Math.max(0, Math.min(bins - 1, Math.floor((point.y - minY) / yStep)));
      const key = `${xIndex}:${yIndex}`;
      densityMap.set(key, (densityMap.get(key) || 0) + 1);
      point.cellKey = key;
    });

    const maxDensity = Math.max(...densityMap.values(), 1);

    return validPoints.map((point) => ({
      ...point,
      density: densityMap.get(point.cellKey) || 1,
      densityRatio: (densityMap.get(point.cellKey) || 1) / maxDensity,
    }));
  }, [rows]);

  const normalPoints = scatterPoints.filter((point) => !point.anomaly);
  const anomalyPoints = scatterPoints.filter((point) => point.anomaly);

  const scatterData = {
    datasets: [
      {
        label: "Market points",
        data: normalPoints,
        backgroundColor: (ctx) => {
          const raw = ctx.raw || {};
          const alpha = 0.12 + (raw.densityRatio || 0) * 0.52;
          return `rgba(56, 189, 248, ${alpha})`;
        },
        borderColor: "rgba(125, 211, 252, 0.4)",
        borderWidth: 1,
        pointRadius: (ctx) => {
          const raw = ctx.raw || {};
          return 2.8 + (raw.densityRatio || 0) * 4.4;
        },
        pointHoverRadius: 6,
        pointHitRadius: 10,
        pointStyle: "circle",
      },
      {
        label: "Anomalies",
        data: anomalyPoints,
        backgroundColor: "#ef4444",
        borderColor: "#fecaca",
        borderWidth: 1.5,
        pointRadius: 7,
        pointHoverRadius: 10,
        pointHitRadius: 14,
        pointStyle: "triangle",
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "nearest", intersect: false },
    plugins: {
      legend: {
        labels: { color: "#eef2ff", boxWidth: 12, boxHeight: 12 },
      },
      tooltip: {
        backgroundColor: "rgba(15, 23, 42, 0.96)",
        titleColor: "#f8fafc",
        bodyColor: "#e2e8f0",
        callbacks: {
          label: (context) => {
            const { x, y, density: count, anomaly, dbscan, isolationForest } = context.raw || {};
            return [
              `Price: Rs.${Number(x).toFixed(2)}`,
              `Volume: ${Math.round(Number(y))}`,
              `Local density: ${count ?? 0}`,
              anomaly ? `Detector: ${getDetectorLabel({ dbscan, isolationForest })}` : "Detector: normal",
            ];
          },
        },
      },
    },
    scales: {
      x: {
        title: { display: true, text: "Price", color: "#cbd5e1" },
        ticks: { color: "#cbd5e1" },
        grid: { color: "rgba(148, 163, 184, 0.14)" },
      },
      y: {
        title: { display: true, text: "Volume", color: "#cbd5e1" },
        ticks: { color: "#cbd5e1", callback: (value) => Number(value).toLocaleString() },
        grid: { color: "rgba(148, 163, 184, 0.14)" },
      },
    },
  };

  return (
    <ChartShell
      eyebrow="2. Scatter density chart"
      title="Price-volume scatter field"
      description="A proper scatter plot with normal points in blue and anomalous rows highlighted in red."
      actionLabel="Fullscreen"
      onAction={toggleFullscreen}
      isFullscreen={isFullscreen}
      frameRef={frameRef}
      frameClassName="density-chart-frame"
      meta={
        <div className="density-meta">
          <span>
            Observations <strong>{rows.length}</strong>
          </span>
          <span>
            Anomalies <strong>{anomalyCount}</strong>
          </span>
        </div>
      }
    >
      <Scatter data={scatterData} options={options} />
    </ChartShell>
  );
}

function AnomalyOverlayChart({ data }) {
  const { frameRef, isFullscreen, toggleFullscreen } = useFullscreenFrame();

  const closeValues = useMemo(
    () => data.map(getValue).filter((v) => Number.isFinite(Number(v))).map(Number),
    [data],
  );

  const stats = useMemo(() => {
    if (!closeValues.length) return { mean: 0, stdDev: 0 };
    const mean = closeValues.reduce((a, b) => a + b, 0) / closeValues.length;
    const variance = closeValues.reduce((acc, value) => acc + (value - mean) ** 2, 0) / closeValues.length;
    return { mean, stdDev: Math.sqrt(variance) };
  }, [closeValues]);

  const labels = data.map(getLabel);
  const closeSeries = data.map((row) => ({ x: getLabel(row), y: getValue(row) }));

  const anomalyPoints = data
    .map((row, index) => {
      const value = Number(getValue(row));
      const state = getAnomalyState(row);
      if (!state.isAnomaly || !Number.isFinite(value)) return null;

      const z = getAnomalyZScore(row, value, stats.mean, stats.stdDev);
      const direction = value - stats.mean >= 0 ? "above" : "below";

      return {
        x: getLabel(row),
        y: value,
        z,
        reason: z == null ? "Anomalous by model signals" : `${Math.abs(z).toFixed(2)}σ ${direction} mean`,
        dbscan: state.dbscan,
        isolationForest: state.isolationForest,
        index,
        ifScore: row.Anomaly_Score_IF ?? row.IF_Anomaly_Score ?? null,
      };
    })
    .filter(Boolean);

  const criticalPoints = anomalyPoints.filter((point) => point.dbscan === -1 && point.isolationForest === -1);
  const densityPoints = anomalyPoints.filter((point) => point.dbscan === -1 && point.isolationForest !== -1);
  const structurePoints = anomalyPoints.filter((point) => point.isolationForest === -1 && point.dbscan !== -1);

  const chartData = {
    labels,
    datasets: [
      {
        label: "Close Price",
        data: closeSeries,
        type: "line",
        borderColor: "#7dd3fc",
        backgroundColor: "rgba(125, 211, 252, 0.1)",
        fill: true,
        tension: 0.2,
        pointRadius: 0,
        borderWidth: 2,
        order: 1,
      },

      {
        label: "Critical (IF + DBSCAN)",
        data: criticalPoints,
        type: "scatter",
        backgroundColor: "#ef4444",
        borderColor: "#ef4444",
        pointRadius: 7,
        pointHoverRadius: 9,
        pointStyle: "rectRounded",
        showLine: false,
        order: 10,
      },
      {
        label: "Density (DBSCAN)",
        data: densityPoints,
        type: "scatter",
        backgroundColor: "#fb923c",
        borderColor: "#fb923c",
        pointRadius: 6,
        pointHoverRadius: 8,
        pointStyle: "circle",
        showLine: false,
        order: 11,
      },
      {
        label: "Structure (IsolationForest)",
        data: structurePoints,
        type: "scatter",
        backgroundColor: "#22c55e",
        borderColor: "#22c55e",
        pointRadius: 6,
        pointHoverRadius: 8,
        pointStyle: "triangle",
        showLine: false,
        order: 12,
      },
    ].filter((dataset) => Array.isArray(dataset.data) && dataset.data.length > 0),
  };

  const options = {
    ...chartOptions((value) => `Rs.${value}`, labels),
    plugins: {
      ...chartOptions(() => "", labels).plugins,
      tooltip: {
        backgroundColor: "rgba(15, 23, 42, 0.96)",
        titleColor: "#f8fafc",
        bodyColor: "#e2e8f0",
        borderColor: "rgba(148, 163, 184, 0.24)",
        borderWidth: 1,
        callbacks: {
          label: (context) => {
            const raw = context.raw || {};
            const value = raw.y != null ? Number(raw.y).toFixed(2) : "n/a";
              const detector =
                raw.dbscan === -1 && raw.isolationForest === -1
                  ? "IF + DBSCAN"
                  : raw.dbscan === -1
                    ? "DBSCAN"
                    : "Isolation Forest";
              const zText = raw.z != null && Number.isFinite(raw.z) ? `${Number(raw.z).toFixed(2)} z-score` : "z-score unavailable";
              const ifScoreText = raw.ifScore != null ? `IF score: ${Number(raw.ifScore).toFixed(3)}` : raw.ifScore === null ? "IF score: n/a" : "IF score: n/a";
              return [
                `${context.dataset.label}: Rs.${value}`,
                `Reason: ${raw.reason || "Anomalous model signal"}`,
                `Reference: ${zText}`,
                `Detector: ${detector}`,
                ifScoreText,
              ];
          },
        },
      },
    },
  };

  return (
    <ChartShell
      eyebrow="3. Anomaly overlay"
      title="Price path with explainable anomaly markers"
      description="Hover each anomaly to see why it is anomalous with sigma and z-score references."
      actionLabel="Fullscreen"
      onAction={toggleFullscreen}
      isFullscreen={isFullscreen}
      frameRef={frameRef}
    >
      <div className="chart-inner">
        <Line data={chartData} options={options} />
      </div>
    </ChartShell>
  );
}

function AnomalyRowsReport({ data }) {
  const closeValues = data
    .map(getValue)
    .filter((v) => Number.isFinite(Number(v)))
    .map(Number);

  const mean = closeValues.length ? closeValues.reduce((a, b) => a + b, 0) / closeValues.length : 0;
  const variance = closeValues.length
    ? closeValues.reduce((acc, value) => acc + (value - mean) ** 2, 0) / closeValues.length
    : 0;
  const stdDev = Math.sqrt(variance);

  const anomalyRows = data
    .map((row, index) => {
      const state = getAnomalyState(row);
      const value = Number(getValue(row));
      if (!state.isAnomaly || !Number.isFinite(value)) return null;

      const z = getAnomalyZScore(row, value, mean, stdDev);
      const direction = value - mean >= 0 ? "above" : "below";
      const sigmaText = z == null ? "n/a" : `${Math.abs(z).toFixed(2)}σ ${direction} mean`;
      const detector =
        state.dbscan === -1 && state.isolationForest === -1
          ? "IF + DBSCAN"
          : state.dbscan === -1
            ? "DBSCAN"
            : "Isolation Forest";
      const ifScore = row.Anomaly_Score_IF ?? row.IF_Anomaly_Score ?? "n/a";

      const rsiVal = row.RSI ?? row.rsi ?? null;
      const bbwVal = row.bb_width ?? row.BB_width ?? row.bbWidth ?? null;

      return {
        index: index + 1,
        time: getLabel(row),
        close: value,
        z,
        sigmaText,
        detector,
        ifScore: typeof ifScore === "number" ? ifScore.toFixed(3) : ifScore,
        rsi: rsiVal != null && Number.isFinite(Number(rsiVal)) ? Number(rsiVal) : null,
        bbWidth: bbwVal != null && Number.isFinite(Number(bbwVal)) ? Number(bbwVal) : null,
      };
    })
    .filter(Boolean);

  return (
    <section className="chart-panel">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">4. Anomalous rows report</p>
          <h3>Flagged rows with reasons</h3>
        </div>
      </div>

      {anomalyRows.length === 0 ? (
        <p className="anomaly-table-empty">No anomalies found in the current result set.</p>
      ) : (
        <div className="anomaly-table-wrap">
          <table className="anomaly-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Time</th>
                <th>Close</th>
                <th>Z-Score</th>
                <th>RSI</th>
                <th>BB width</th>
                <th>IF Score</th>
                <th>Detector</th>
              </tr>
            </thead>
            <tbody>
              {anomalyRows.map((row) => (
                <tr key={`${row.time}-${row.index}`}>
                  <td>{row.index}</td>
                  <td>{row.time || "—"}</td>
                  <td>{row.close.toFixed(2)}</td>
                  <td>{row.z == null ? "n/a" : Number(row.z).toFixed(2)}</td>
                  <td>{row.rsi == null ? '—' : Number(row.rsi).toFixed(2)}</td>
                  <td>{row.bbWidth == null ? '—' : Number(row.bbWidth).toFixed(2)}</td>
                  <td>{row.ifScore}</td>
                  <td>{row.detector}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default function AnomalyChart({ data = [] }) {
  return (
    <>
      <TechnicalChart data={data} />
      <DensityChart data={data} />
      <AnomalyOverlayChart data={data} />
      <AnomalyRowsReport data={data} />
      <div className="chart-card-footer">
        <p>The views are ordered for interpretation: technical baseline, density distribution, explainable anomalies, and anomalous rows.</p>
      </div>
    </>
  );
}
