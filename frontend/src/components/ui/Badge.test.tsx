/**
 * Tests for Badge — status indicator with dot + label.
 *
 * Covers:
 * - Each canonical status maps to the expected default label.
 * - `children` prop overrides the default label.
 * - The status dot span is present (aria-hidden).
 * - `className` prop is forwarded.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Badge } from "./Badge";

describe("Badge", () => {
  it("shows 'Running' for running status", () => {
    render(<Badge status="running" />);
    expect(screen.getByText("Running")).toBeInTheDocument();
  });

  it("shows 'Done' for complete status", () => {
    render(<Badge status="complete" />);
    expect(screen.getByText("Done")).toBeInTheDocument();
  });

  it("shows 'Queued' for queued status", () => {
    render(<Badge status="queued" />);
    expect(screen.getByText("Queued")).toBeInTheDocument();
  });

  it("shows 'Errored' for error status", () => {
    render(<Badge status="error" />);
    expect(screen.getByText("Errored")).toBeInTheDocument();
  });

  it("shows 'Review' for awaiting_review status", () => {
    render(<Badge status="awaiting_review" />);
    expect(screen.getByText("Review")).toBeInTheDocument();
  });

  it("shows 'Cancelled' for cancelled status", () => {
    render(<Badge status="cancelled" />);
    expect(screen.getByText("Cancelled")).toBeInTheDocument();
  });

  it("overrides label with children", () => {
    render(<Badge status="running">Custom label</Badge>);
    expect(screen.getByText("Custom label")).toBeInTheDocument();
    expect(screen.queryByText("Running")).not.toBeInTheDocument();
  });

  it("forwards className to the span", () => {
    const { container } = render(
      <Badge status="queued" className="test-class" />,
    );
    expect(container.firstChild).toHaveClass("test-class");
  });

  it("renders a dot span with aria-hidden", () => {
    const { container } = render(<Badge status="running" />);
    const dot = container.querySelector("[aria-hidden]");
    expect(dot).not.toBeNull();
  });
});
