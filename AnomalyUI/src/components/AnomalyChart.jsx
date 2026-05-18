import { Line } from "react-chartjs-2";
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

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, ScatterController, Tooltip, Legend, Filler);

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

function chartOptions(yCallback) {
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
        callbacks: {
          label: function (context) {
            const raw = context.raw;
            const value = raw && raw.y !== undefined ? raw.y : context.parsed.y;
            const z = raw && raw.z !== undefined ? raw.z : null;
            let label = `${context.dataset.label}: Rs.${value}`;
            if (z != null && !Number.isNaN(z)) label += ` — ${z.toFixed(2)}σ`;
            return label;
          },
        },
      },
    },
    scales: {
      x: {
        ticks: { color: "#cbd5e1", maxRotation: 0, autoSkip: true, maxTicksLimit: 10 , display:false},
        grid: { display: false },
      },
      y: {
        ticks: { color: "#cbd5e1", callback: yCallback },
        grid: { color: "rgba(148, 163, 184, 0.14)" },
      },
    },
  };
}

function buildDensityMatrix(data, xKey, yKey, bins = 8) {
  const points = data
    .map((row) => ({ x: Number(row[xKey]), y: Number(row[yKey]) }))
    .filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y));

  if (points.length === 0) {
    return { cells: [], max: 0 };
  }

  const xs = points.map((point) => point.x);
  const ys = points.map((point) => point.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const xStep = (maxX - minX || 1) / bins;
  const yStep = (maxY - minY || 1) / bins;

  const matrix = Array.from({ length: bins }, () => Array.from({ length: bins }, () => 0));
  points.forEach((point) => {
    const xIndex = Math.max(0, Math.min(bins - 1, Math.floor((point.x - minX) / xStep)));
    const yIndex = Math.max(0, Math.min(bins - 1, Math.floor((point.y - minY) / yStep)));
    matrix[bins - 1 - yIndex][xIndex] += 1;
  });

  return { cells: matrix, max: Math.max(...matrix.flat()) };
}

function TechnicalChart({ data }) {
  const labels = data.map(getLabel);
  const closeSeries = data.map(getValue);
  const sma10 = data.map((row) => row.SMA_10 ?? null);
  const sma20 = data.map((row) => row.SMA_20 ?? null);
  const sma50 = data.map((row) => row.SMA_50 ?? null);

  const chartData = {
    labels,
    datasets: [
      { label: "Close Price", data: closeSeries, borderColor: "#57c7ff", backgroundColor: "rgba(87, 199, 255, 0.14)", fill: true, tension: 0.25, pointRadius: 0, borderWidth: 2 },
      { label: "SMA 10", data: sma10, borderColor: "#fcbf49", borderDash: [6, 4], pointRadius: 0, tension: 0.2 },
      { label: "SMA 20", data: sma20, borderColor: "#8be9fd", borderDash: [6, 4], pointRadius: 0, tension: 0.2 },
      { label: "SMA 50", data: sma50, borderColor: "#a855f7", borderDash: [10, 6], pointRadius: 0, tension: 0.2 },
    ].filter((dataset) => dataset.data.some((value) => value !== null && value !== undefined)),
  };

  return (
    <section className="chart-panel">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">1. Technical reference</p>
          <h3>Price, moving averages, and baseline context</h3>
          <p>Use this first chart to establish the technical reference before interpreting density or anomaly flags.</p>
        </div>
      </div>
      <div className="chart-frame compact-chart">
        <Line data={chartData} options={chartOptions((value) => `Rs.${value}`)} />
      </div>
    </section>
  );
}

function DensityMatrix({ data }) {
  const density = buildDensityMatrix(data.filter((row) => Number.isFinite(Number(row.close ?? row.price)) && Number.isFinite(Number(row.volume))), "close", "volume", 8);
  const points = data.filter((row) => Number.isFinite(Number(row.close ?? row.price)) && Number.isFinite(Number(row.volume)));
  const anomalyCount = data.filter((row) => row.cluster === -1).length;
  const max = density.max || 1;

  return (
    <section className="chart-panel">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">2. DBSCAN density matrix</p>
          <h3>Price vs. volume concentration map</h3>
          <p>A density-style matrix showing where observations cluster in price-volume space before anomaly filtering.</p>
        </div>
      </div>
      <div className="density-meta">
        <span>Observations <strong>{points.length}</strong></span>
        <span>Anomalies <strong>{anomalyCount}</strong></span>
      </div>
      <div className="density-matrix-shell">
        <div className="density-axis density-axis-y">Volume</div>
        <div className="density-matrix-grid">
          {density.cells.map((row, rowIndex) =>
            row.map((count, colIndex) => {
              const intensity = count / max;
              return (
                <div
                  key={`${rowIndex}-${colIndex}`}
                  className="density-cell"
                  style={{
                    background: `rgba(56, 189, 248, ${0.08 + intensity * 0.72})`,
                    borderColor: `rgba(125, 211, 252, ${0.12 + intensity * 0.6})`,
                  }}
                  title={`Density: ${count}`}
                >
                  {count > 0 ? count : ""}
                </div>
              );
            }),
          )}
        </div>
        <div className="density-axis density-axis-x">Price</div>
      </div>
    </section>
  );
}

function AnomalyOverlayChart({ data }) {
  const labels = data.map(getLabel);
  const closeSeries = data.map((row) => ({ x: getLabel(row), y: getValue(row) }));

  const anomalyPoints = data
    .map((row) => {
      const value = getValue(row);
      const state = getAnomalyState(row);
      if (!state.isAnomaly || value == null) return null;
      return {
        x: getLabel(row),
        y: value,
        z: row.Anomaly_Z_Score != null ? Number(row.Anomaly_Z_Score) : null,
        dbscan: state.dbscan,
        isolationForest: state.isolationForest,
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

  return (
    <section className="chart-panel">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">3. Anomaly overlay</p>
          <h3>Price path with flagged anomalies</h3>
          <p>The final graph overlays anomaly markers so unusual points are easy to inspect after the reference charts.</p>
        </div>
      </div>
      <div className="chart-frame compact-chart">
        <Line data={chartData} options={chartOptions((value) => `Rs.${value}`)} />
      </div>
    </section>
  );
}

export default function AnomalyChart({ data = [] }) {
  return (
    <div className="chart-stack">
      <TechnicalChart data={data} />
      <DensityMatrix data={data} />
      <AnomalyOverlayChart data={data} />
      <div className="chart-card-footer">
        <p>The three views are ordered for interpretation: technical baseline first, DBSCAN density second, anomaly flags last.</p>
      </div>
    </div>
  );
}
