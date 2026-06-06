import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import AnalysisHistory from "../components/AnalysisHistory";
import * as api from "../api";
import { vi } from "vitest";

vi.mock("../api", () => ({
  fetchAnalyses: vi.fn(),
  fetchAnalysisData: vi.fn(),
  toggleFavorite: vi.fn(),
}));

describe("AnalysisHistory", () => {
  beforeEach(() => {
    api.fetchAnalyses.mockResolvedValue([
      { id: 1, stock: "NABIL", executed_at: new Date().toISOString(), mode: "Static", timeframe: "1D", status: "success", is_favorite: false },
    ]);
    api.fetchAnalysisData.mockResolvedValue({ data: [] });
    api.toggleFavorite.mockResolvedValue({ id: 1, is_favorite: true });
  });

  it("renders and calls onSelect when View clicked", async () => {
    const onSelect = vi.fn();
    render(<AnalysisHistory token="tok" onSelect={onSelect} />);
    await waitFor(() => expect(api.fetchAnalyses).toHaveBeenCalled());
    const viewBtn = await screen.findByText("View");
    fireEvent.click(viewBtn);
    await waitFor(() => expect(api.fetchAnalysisData).toHaveBeenCalled());
    expect(onSelect).toHaveBeenCalled();
  });

  it("toggles favorite", async () => {
    render(<AnalysisHistory token="tok" onSelect={() => {}} />);
    await waitFor(() => expect(api.fetchAnalyses).toHaveBeenCalled());
    const favBtn = await screen.findByText(/Favorite/);
    fireEvent.click(favBtn);
    await waitFor(() => expect(api.toggleFavorite).toHaveBeenCalled());
  });
});
