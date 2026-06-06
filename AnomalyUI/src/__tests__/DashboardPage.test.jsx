import { render, screen, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import DashboardPage from "../pages/Dashboard";
import { vi } from "vitest";

vi.mock("../components/FavoritesPanel", () => ({
  default: () => <div data-testid="favorites-panel">Favorites Panel</div>,
}));

describe("DashboardPage", () => {
  const mockUser = {
    id: 1,
    username: "analyst",
    role: "analyst",
  };

  const mockConfig = {
    stock: "API",
    timeframe: "1D",
    start_date: "2024-01-01",
    end_date: "2026-01-01",
    features: ["RSI", "volume"],
  };

  const mockResults = {
    data: [
      { date: "2024-01-01", close: 100, cluster: -1 },
      { date: "2024-01-02", close: 101, cluster: 0 },
    ],
    models: {
      DBSCAN: { n_clusters: 2 },
      IsolationForest: { contamination: 0.1 },
    },
  };

  it("renders dashboard with user role", () => {
    render(
      <BrowserRouter>
        <DashboardPage
          user={mockUser}
          lastConfig={mockConfig}
          results={mockResults}
          onOpenLastRun={() => {}}
        />
      </BrowserRouter>
    );
    expect(screen.getByText(/Overview of the current anomaly workspace/i)).toBeInTheDocument();
    expect(screen.getByText(/Role: analyst/i)).toBeInTheDocument();
  });

  it("displays latest analysis information", () => {
    render(
      <BrowserRouter>
        <DashboardPage
          user={mockUser}
          lastConfig={mockConfig}
          results={mockResults}
          onOpenLastRun={() => {}}
        />
      </BrowserRouter>
    );
    expect(screen.getByText("API")).toBeInTheDocument();
    expect(screen.getByText("1D")).toBeInTheDocument();
    expect(screen.getByText("2024-01-01 – 2026-01-01")).toBeInTheDocument();
  });

  it("displays anomaly count from results", () => {
    render(
      <BrowserRouter>
        <DashboardPage
          user={mockUser}
          lastConfig={mockConfig}
          results={mockResults}
          onOpenLastRun={() => {}}
        />
      </BrowserRouter>
    );
    expect(screen.getByText("1")).toBeInTheDocument(); // 1 anomaly with cluster -1
  });

  it("displays metrics count", () => {
    render(
      <BrowserRouter>
        <DashboardPage
          user={mockUser}
          lastConfig={mockConfig}
          results={mockResults}
          onOpenLastRun={() => {}}
        />
      </BrowserRouter>
    );
    expect(screen.getByText("2")).toBeInTheDocument(); // 2 metrics groups
  });

  it("has quick action buttons", () => {
    const onOpenLastRun = vi.fn();
    render(
      <BrowserRouter>
        <DashboardPage
          user={mockUser}
          lastConfig={mockConfig}
          results={mockResults}
          onOpenLastRun={onOpenLastRun}
        />
      </BrowserRouter>
    );
    expect(screen.getByText(/Run a new analysis/i)).toBeInTheDocument();
    expect(screen.getByText(/Review latest results/i)).toBeInTheDocument();
  });

  it("shows admin actions only for admin users", () => {
    const adminUser = { ...mockUser, role: "admin" };
    render(
      <BrowserRouter>
        <DashboardPage
          user={adminUser}
          lastConfig={mockConfig}
          results={mockResults}
          onOpenLastRun={() => {}}
        />
      </BrowserRouter>
    );
    expect(screen.getByText(/Manage data/i)).toBeInTheDocument();
    expect(screen.getByText(/Manage users/i)).toBeInTheDocument();
  });

  it("does not show admin actions for analyst users", () => {
    render(
      <BrowserRouter>
        <DashboardPage
          user={mockUser}
          lastConfig={mockConfig}
          results={mockResults}
          onOpenLastRun={() => {}}
        />
      </BrowserRouter>
    );
    expect(screen.queryByText(/Manage data/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Manage users/i)).not.toBeInTheDocument();
  });

  it("handles missing results gracefully", () => {
    render(
      <BrowserRouter>
        <DashboardPage
          user={mockUser}
          lastConfig={mockConfig}
          results={null}
          onOpenLastRun={() => {}}
        />
      </BrowserRouter>
    );
    expect(screen.getByText(/Overview of the current anomaly workspace/i)).toBeInTheDocument();
  });
});
