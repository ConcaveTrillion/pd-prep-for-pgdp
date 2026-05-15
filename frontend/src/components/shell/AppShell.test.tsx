import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AppShell } from "./AppShell";

describe("AppShell", () => {
  it("renders header, main, and footer slots", () => {
    render(
      <AppShell
        header={<div>header content</div>}
        footer={<div>footer content</div>}
      >
        <div>main content</div>
      </AppShell>,
    );

    expect(screen.getByText("header content")).toBeInTheDocument();
    expect(screen.getByText("main content")).toBeInTheDocument();
    expect(screen.getByText("footer content")).toBeInTheDocument();
  });

  it('has data-testid="app-shell" by default', () => {
    render(
      <AppShell header={<div />} footer={<div />}>
        <div />
      </AppShell>,
    );

    expect(screen.getByTestId("app-shell")).toBeInTheDocument();
  });

  it("accepts a custom data-testid", () => {
    render(
      <AppShell header={<div />} footer={<div />} data-testid="custom-shell">
        <div />
      </AppShell>,
    );

    expect(screen.getByTestId("custom-shell")).toBeInTheDocument();
    expect(screen.queryByTestId("app-shell")).toBeNull();
  });

  it("header slot renders inside a <header> element", () => {
    const { container } = render(
      <AppShell header={<span data-testid="hd">HDR</span>} footer={<div />}>
        <div />
      </AppShell>,
    );

    const headerEl = container.querySelector("header");
    expect(headerEl).not.toBeNull();
    expect(headerEl).toContainElement(screen.getByTestId("hd"));
  });

  it("footer slot renders inside a <footer> element", () => {
    const { container } = render(
      <AppShell header={<div />} footer={<span data-testid="ft">FTR</span>}>
        <div />
      </AppShell>,
    );

    const footerEl = container.querySelector("footer");
    expect(footerEl).not.toBeNull();
    expect(footerEl).toContainElement(screen.getByTestId("ft"));
  });

  it("children render inside a <main> element", () => {
    const { container } = render(
      <AppShell header={<div />} footer={<div />}>
        <span data-testid="mn">MAIN</span>
      </AppShell>,
    );

    const mainEl = container.querySelector("main");
    expect(mainEl).not.toBeNull();
    expect(mainEl).toContainElement(screen.getByTestId("mn"));
  });
});
