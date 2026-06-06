import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import LoginPage from "../pages/LoginPage";
import * as api from "../api";
import { vi } from "vitest";

vi.mock("../api", () => ({
  login: vi.fn(),
}));

describe("LoginPage", () => {
  beforeEach(() => {
    api.login.mockResolvedValue({ access_token: "test_token_123" });
  });

  it("renders login form", () => {
    render(
      <BrowserRouter>
        <LoginPage onSuccess={() => {}} />
      </BrowserRouter>
    );
    expect(screen.getByText(/Sign in to Anomaly Engine/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    expect(screen.getByText(/Sign in/i)).toBeInTheDocument();
  });

  it("calls login with correct credentials", async () => {
    const onSuccess = vi.fn();
    render(
      <BrowserRouter>
        <LoginPage onSuccess={onSuccess} />
      </BrowserRouter>
    );

    const usernameInput = screen.getByDisplayValue("");
    const passwordInput = screen.getAllByDisplayValue("")[1];
    const submitBtn = screen.getByText(/Sign in/i);

    fireEvent.change(usernameInput, { target: { value: "analyst" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(api.login).toHaveBeenCalledWith("analyst", "password123");
    });
  });

  it("handles login errors", async () => {
    api.login.mockRejectedValueOnce(new Error("Invalid credentials"));
    render(
      <BrowserRouter>
        <LoginPage onSuccess={() => {}} />
      </BrowserRouter>
    );

    const usernameInput = screen.getByDisplayValue("");
    const passwordInput = screen.getAllByDisplayValue("")[1];
    const submitBtn = screen.getByText(/Sign in/i);

    fireEvent.change(usernameInput, { target: { value: "analyst" } });
    fireEvent.change(passwordInput, { target: { value: "wrongpassword" } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/Invalid credentials/i)).toBeInTheDocument();
    });
  });

  it("shows loading state during authentication", async () => {
    api.login.mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(() => resolve({ access_token: "token" }), 100)
        )
    );
    render(
      <BrowserRouter>
        <LoginPage onSuccess={() => {}} />
      </BrowserRouter>
    );

    const usernameInput = screen.getByDisplayValue("");
    const passwordInput = screen.getAllByDisplayValue("")[1];
    const submitBtn = screen.getByText(/Sign in/i);

    fireEvent.change(usernameInput, { target: { value: "analyst" } });
    fireEvent.change(passwordInput, { target: { value: "password" } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/Authenticating/i)).toBeInTheDocument();
    });
  });
});
