import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // bg tokens
        "bg-page": "var(--bg-page)",
        "bg-surface": "var(--bg-surface)",
        "bg-raised": "var(--bg-raised)",
        "bg-sunk": "var(--bg-sunk)",
        // border tokens
        "border-1": "var(--border-1)",
        "border-2": "var(--border-2)",
        "border-3": "var(--border-3)",
        // ink tokens
        "ink-1": "var(--ink-1)",
        "ink-2": "var(--ink-2)",
        "ink-3": "var(--ink-3)",
        "ink-4": "var(--ink-4)",
        // accent
        accent: "var(--accent)",
        "accent-ink": "var(--accent-ink)",
        // brand
        brand: "var(--brand)",
        "brand-ink": "var(--brand-ink)",
        // status
        "status-done": "var(--status-done)",
        "status-running": "var(--status-running)",
        "status-queued": "var(--status-queued)",
        "status-error": "var(--status-error)",
        "status-review": "var(--status-review)",
        "status-done-bg": "var(--status-done-bg)",
        "status-running-bg": "var(--status-running-bg)",
        "status-queued-bg": "var(--status-queued-bg)",
        "status-error-bg": "var(--status-error-bg)",
        "status-review-bg": "var(--status-review-bg)",
        // stage
        "stage-clean": "var(--stage-clean)",
        "stage-dirty": "var(--stage-dirty)",
        "stage-not-run": "var(--stage-not-run)",
        "stage-running": "var(--stage-running)",
        "stage-failed": "var(--stage-failed)",
        "stage-na": "var(--stage-na)",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      fontSize: {
        xxs: ["10px", { lineHeight: "1.2" }],
        xs2: ["11px", { lineHeight: "1.3" }],
      },
    },
  },
  plugins: [],
} satisfies Config;
