import React from "react"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { BrowserRouter } from "react-router-dom"
import RegisterPage from "../pages/RegisterPage"
import * as api from "../api"
import { vi } from "vitest"

vi.mock("../api", () => ({
  registerRequest: vi.fn(),
  verifyOTP: vi.fn(),
}))

describe("RegisterPage", () => {
  beforeEach(() => {
    api.registerRequest.mockResolvedValue({ message: "OTP sent to your email." })
    api.verifyOTP.mockResolvedValue({ username: "newuser", email_verified: true })
  })

  it("renders registration form", () => {
    render(
      <BrowserRouter>
        <RegisterPage />
      </BrowserRouter>
    )
    expect(screen.getByText(/Create an account/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Username/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^Password/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Confirm password/i)).toBeInTheDocument()
  })

  it("validates password match", async () => {
    render(
      <BrowserRouter>
        <RegisterPage />
      </BrowserRouter>
    )
    const usernameInput = screen.getByLabelText(/Username/i)
    const emailInput = screen.getByLabelText(/Email/i)
    const passwordInput = screen.getByLabelText(/^Password/i)
    const confirmInput = screen.getByLabelText(/Confirm password/i)
    const submitBtn = screen.getByText(/Create account/i)

    fireEvent.change(usernameInput, { target: { value: "newuser" } })
    fireEvent.change(emailInput, { target: { value: "newuser@example.com" } })
    fireEvent.change(passwordInput, { target: { value: "password123" } })
    fireEvent.change(confirmInput, { target: { value: "password456" } })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(screen.getByText(/Passwords do not match/i)).toBeInTheDocument()
    })
  })

  it("calls registerRequest and shows OTP step success", async () => {
    render(
      <BrowserRouter>
        <RegisterPage />
      </BrowserRouter>
    )
    const usernameInput = screen.getByLabelText(/Username/i)
    const emailInput = screen.getByLabelText(/Email/i)
    const passwordInput = screen.getByLabelText(/^Password/i)
    const confirmInput = screen.getByLabelText(/Confirm password/i)
    const submitBtn = screen.getByText(/Create account/i)

    fireEvent.change(usernameInput, { target: { value: "newuser" } })
    fireEvent.change(emailInput, { target: { value: "newuser@example.com" } })
    fireEvent.change(passwordInput, { target: { value: "password123" } })
    fireEvent.change(confirmInput, { target: { value: "password123" } })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(api.registerRequest).toHaveBeenCalledWith(
        "newuser",
        "newuser@example.com",
        "password123"
      )
    })
    await waitFor(() => {
      expect(screen.getByText(/OTP sent to your email/i)).toBeInTheDocument()
    })
  })
})
