/**
 * Smoke test for `vite-tsconfig-paths` (§13a step 3).
 *
 * Confirms the `@/*` → `src/*` alias declared in `tsconfig.app.json` is
 * picked up by both Vite (production build) and Vitest (test runner).
 * A failing import here is the canary that the plugin is wired into
 * the wrong config or that `tsconfig.app.json`'s `paths` block was
 * dropped by a refactor.
 *
 * The test deliberately imports a stable, side-effect-free module
 * (`marquee` is a pure-function geometry helper); if that module is
 * ever renamed or moved, swap the import target — the assertion below
 * is the canary, not the math.
 */
import { describe, expect, it } from "vitest";
import { normaliseMarquee } from "@/lib/marquee";

describe("vite-tsconfig-paths plugin", () => {
  it("resolves `@/*` to `src/*` in the test runner", () => {
    // Resolving `@/lib/marquee` through the alias and exercising one
    // export proves the plugin is wired into vitest.config.ts and the
    // `tsconfig.app.json` `paths` block is intact.
    expect(typeof normaliseMarquee).toBe("function");
  });
});
