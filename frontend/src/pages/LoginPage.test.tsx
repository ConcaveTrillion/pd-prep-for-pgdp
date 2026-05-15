/**
 * Minimal smoke test for LoginPage.
 *
 * LoginPage immediately kicks off a PKCE redirect on mount, so we mock
 * window.__ENV__ to an empty object so the useEffect short-circuits with an
 * error message and never calls window.location.href.  We only assert that
 * the "Sign in" heading is present (structural proof the Card renders).
 */
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { LoginPage } from "./LoginPage";

describe("LoginPage", () => {
  it("renders the Sign in heading", () => {
    // No JWT_ISSUER → useEffect sets an error and never redirects.
    (window as any).__ENV__ = {};
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );
    expect(
      screen.getByRole("heading", { name: /sign in/i }),
    ).toBeInTheDocument();
  });
});
