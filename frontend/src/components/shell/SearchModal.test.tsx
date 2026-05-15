/**
 * Tests for SearchModal — global search dialog (hifi P1-2).
 *
 * Covers:
 * - Renders without crashing (closed by default, no visible content).
 * - Opens when uiPrefs.searchOpen is set to true.
 * - Closes when the X button is clicked (onOpenChange called with false).
 * - Shows "Navigate to a project" message when no project route is active.
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useUiPrefs } from "../../stores/uiPrefs";
import { SearchModal } from "./SearchModal";

// react-hotkeys-hook fires keyboard listeners; stub it out to keep tests fast.
vi.mock("react-hotkeys-hook", () => ({
  useHotkeys: vi.fn(),
}));

function renderWithProviders(ui: ReactElement, { initialPath = "/" } = {}) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
    </MemoryRouter>,
  );
}

describe("SearchModal", () => {
  beforeEach(() => {
    useUiPrefs.setState({ theme: "light", searchOpen: false });
  });

  it("renders without crashing and is closed by default", () => {
    renderWithProviders(<SearchModal />);
    // Dialog content is not in DOM when closed (Radix Dialog Portal).
    expect(screen.queryByTestId("search-modal")).not.toBeInTheDocument();
  });

  it("shows modal content when searchOpen is true", () => {
    useUiPrefs.setState({ searchOpen: true });
    renderWithProviders(<SearchModal />);
    expect(screen.getByTestId("search-modal")).toBeInTheDocument();
  });

  it("shows 'Navigate to a project' when not on a project route", () => {
    useUiPrefs.setState({ searchOpen: true });
    renderWithProviders(<SearchModal />, { initialPath: "/" });
    expect(
      screen.getByText(/navigate to a project to search/i),
    ).toBeInTheDocument();
  });

  it("shows search-panel when on a project route", () => {
    useUiPrefs.setState({ searchOpen: true });
    renderWithProviders(<SearchModal />, {
      initialPath: "/projects/proj-abc",
    });
    expect(screen.getByTestId("search-panel")).toBeInTheDocument();
  });

  it("closes when the X button is clicked", async () => {
    useUiPrefs.setState({ searchOpen: true });
    const user = userEvent.setup();
    renderWithProviders(<SearchModal />);

    await user.click(screen.getByRole("button", { name: /close/i }));
    expect(useUiPrefs.getState().searchOpen).toBe(false);
  });

  it("accepts a custom data-testid", () => {
    useUiPrefs.setState({ searchOpen: true });
    renderWithProviders(<SearchModal data-testid="my-search" />);
    expect(screen.getByTestId("my-search")).toBeInTheDocument();
  });
});
