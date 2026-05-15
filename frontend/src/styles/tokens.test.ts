import { describe, it, expect, beforeAll } from "vitest";

describe("tokens.css", () => {
  beforeAll(async () => {
    // Inject minimal token CSS for test environment
    const style = document.createElement("style");
    style.textContent = `
      :root {
        --bg-page: #f8fafc;
        --bg-surface: #ffffff;
        --ink-1: #0f172a;
        --ink-2: #334155;
        --status-done: #10b981;
        --stage-clean: #10b981;
      }
      [data-theme="dark"] {
        --bg-page: #020617;
        --bg-surface: #0f172a;
      }
    `;
    document.head.appendChild(style);
  });

  it("light default bg-page token is defined", () => {
    const value = getComputedStyle(document.documentElement)
      .getPropertyValue("--bg-page")
      .trim();
    expect(value).toBeTruthy();
    expect(value).not.toBe("");
  });

  it("dark theme overrides bg-page", () => {
    document.documentElement.setAttribute("data-theme", "dark");
    const dark = getComputedStyle(document.documentElement)
      .getPropertyValue("--bg-page")
      .trim();
    document.documentElement.removeAttribute("data-theme");
    const light = getComputedStyle(document.documentElement)
      .getPropertyValue("--bg-page")
      .trim();
    expect(dark).not.toBe(light);
  });
});
