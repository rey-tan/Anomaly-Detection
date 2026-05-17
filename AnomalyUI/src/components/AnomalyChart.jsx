import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler);

function formatDate(value) {
  return value ? new Date(value).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "";
}

export default function AnomalyChart({ data = [] }) {
  const labels = data.map((row) => row.date || row.transaction_time || "");
  const closeSeries = data.map((row) => row.close ?? row.price ?? null);
  const anomalies = data.map((row) => (row.cluster === -1 ? row.close ?? row.price ?? null : null));
  const sma10 = data.map((row) => row.SMA_10 ?? null);
  const sma20 = data.map((row) => row.SMA_20 ?? null);
  const sma50 = data.map((row) => row.SMA_50 ?? null);

  const chartData = {
    labels,
    datasets: [
      {
        label: "Close Price",
        data: closeSeries,
        borderColor: "#57c7ff",
        backgroundColor: "rgba(87, 199, 255, 0.12)",
        fill: true,
        tension: 0.2,
        pointRadius: 0,
        borderWidth: 2,
      },
      {
        label: "SMA 10",
        data: sma10,
        borderColor: "#fcbf49",
        borderDash: [6, 4],
        pointRadius: 0,
        tension: 0.2,
      },
      {
        label: "SMA 20",
        data: sma20,
        borderColor: "#8be9fd",
        borderDash: [6, 4],
        pointRadius: 0,
        tension: 0.2,
      },
      {
        label: "SMA 50",
        data: sma50,
        borderColor: "#a855f7",
        borderDash: [10, 6],
        pointRadius: 0,
        tension: 0.2,
      },
      {
        label: "Anomaly",
        data: anomalies,
        borderColor: "#ff5c83",
        backgroundColor: "rgba(255, 92, 131, 0.8)",
        pointRadius: 5,
        pointStyle: "rectRounded",
        showLine: false,
      },
    ].filter((dataset) => dataset.data.some((value) => value !== null && value !== undefined)),
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: "nearest",
      intersect: false,
    },
    plugins: {
      legend: {
        position: "top",
        labels: {
          color: "#eef2ff",
          boxWidth: 12,
          boxHeight: 12,
        },
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
        ticks: {
          color: "#cbd5e1",
          maxRotation: 0,
          autoSkip: true,
          maxTicksLimit: 12,
        },
        grid: {
          display: false,
        },
      },
      y: {
        ticks: {
          color: "#cbd5e1",
          callback: (value) => `$${value}`,
        },
        grid: {
          color: "rgba(148, 163, 184, 0.14)",
        },
      },
    },
  };

  return (
    <div className="chart-card">
      <div className="section-heading">
        <div>
          <h2>Price & anomaly chart</h2>
          <p>Close price with moving averages and anomaly markers.</p>
        </div>
      </div>
      <div className="chart-frame">
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
}
