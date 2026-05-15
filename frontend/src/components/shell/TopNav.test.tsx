import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { TopNav } from "./TopNav";

function renderNav(props: React.ComponentProps<typeof TopNav> = {}) {
  return render(
    <MemoryRouter>
      <TopNav {...props} />
    </MemoryRouter>,
  );
}

describe("TopNav", () => {
  it('renders brand text "pgdp-prep"', () => {
    renderNav();
    expect(screen.getByText("pgdp-prep")).toBeInTheDocument();
  });

  it('renders brand glyph "p"', () => {
    renderNav();
    // The amber glyph span contains exactly the letter "p"
    const glyphs = screen.getAllByText("p");
    // At least one should be the brand glyph (a standalone "p" node)
    expect(glyphs.length).toBeGreaterThan(0);
  });

  it('renders search pill with "Search projects…"', () => {
    renderNav();
    expect(screen.getByText("Search projects…")).toBeInTheDocument();
  });

  it("search pill has accessible label", () => {
    renderNav();
    expect(screen.getByRole("button", { name: /search/i })).toBeInTheDocument();
  });

  it("renders rightSlot content", () => {
    renderNav({ rightSlot: <span data-testid="right-thing">Bell</span> });
    expect(screen.getByTestId("right-thing")).toBeInTheDocument();
  });

  it("renders breadcrumb when provided", () => {
    renderNav({ breadcrumb: <span>My Project</span> });
    expect(screen.getByText("My Project")).toBeInTheDocument();
    // Separator slash also appears
    expect(screen.getByText("/")).toBeInTheDocument();
  });

  it("does not render breadcrumb separator when breadcrumb is absent", () => {
    renderNav();
    expect(screen.queryByText("/")).toBeNull();
  });

  it('has data-testid="top-nav" by default', () => {
    renderNav();
    expect(screen.getByTestId("top-nav")).toBeInTheDocument();
  });

  it("accepts a custom data-testid", () => {
    renderNav({ "data-testid": "custom-nav" });
    expect(screen.getByTestId("custom-nav")).toBeInTheDocument();
    expect(screen.queryByTestId("top-nav")).toBeNull();
  });

  it("renders centerSlot when provided, hiding the default search pill", () => {
    renderNav({ centerSlot: <input placeholder="custom search" /> });
    expect(screen.getByPlaceholderText("custom search")).toBeInTheDocument();
    expect(screen.queryByText("Search projects…")).toBeNull();
  });
});
