import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PageHeader } from "./PageHeader";

describe("PageHeader", () => {
  it("renders the title", () => {
    render(<PageHeader title="Projects" />);
    expect(
      screen.getByRole("heading", { level: 1, name: "Projects" }),
    ).toBeInTheDocument();
  });

  it("renders description when provided", () => {
    render(<PageHeader title="Projects" description="Manage your projects" />);
    expect(screen.getByText("Manage your projects")).toBeInTheDocument();
  });

  it("does not render a description element when description is omitted", () => {
    render(<PageHeader title="Projects" />);
    expect(screen.queryByText("Manage your projects")).toBeNull();
  });

  it("renders actions slot when provided", () => {
    render(
      <PageHeader
        title="Projects"
        actions={<button type="button">New project</button>}
      />,
    );
    expect(
      screen.getByRole("button", { name: "New project" }),
    ).toBeInTheDocument();
  });

  it("uses data-testid='page-header' by default", () => {
    const { container } = render(<PageHeader title="Projects" />);
    expect(
      container.querySelector('[data-testid="page-header"]'),
    ).toBeInTheDocument();
  });

  it("accepts a custom data-testid", () => {
    const { container } = render(
      <PageHeader title="Projects" data-testid="custom-header" />,
    );
    expect(
      container.querySelector('[data-testid="custom-header"]'),
    ).toBeInTheDocument();
    expect(container.querySelector('[data-testid="page-header"]')).toBeNull();
  });
});
