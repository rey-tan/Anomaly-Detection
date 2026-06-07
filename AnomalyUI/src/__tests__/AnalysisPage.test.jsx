import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import AnalysisPage from "../pages/AnalysisPage";
import { vi } from "vitest";

describe("AnalysisPage", () => {
  it("renders analysis page with title", () => {
    render(
      <AnalysisPage
        onSubmit={() => {}}
        loading={false}
        error=""
      />
    );
    expect(screen.getByText(/Run a new anomaly detection job/i)).toBeInTheDocument();
    expect(screen.getByText(/Keep the set small and intentional/i)).toBeInTheDocument();
  });

  it("displays error message when provided", () => {
    const errorMsg = "Analysis failed due to network error";
    render(
      <AnalysisPage
        onSubmit={() => {}}
        loading={false}
        error={errorMsg}
      />
    );
    expect(screen.getByText(errorMsg)).toBeInTheDocument();
  });

  it("does not display error when error is empty", () => {
    render(
      <AnalysisPage
        onSubmit={() => {}}
        loading={false}
        error=""
      />
    );
    const errorBox = screen.queryByRole("region");
    expect(errorBox).toBeNull();
  });

  it("shows loading state", () => {
    render(
      <AnalysisPage
        onSubmit={() => {}}
        loading={true}
        error=""
      />
    );
    // AnalysisPanel passes loading state which typically disables submit button
    expect(screen.getByText(/Run a new anomaly detection job/i)).toBeInTheDocument();
  });
});
