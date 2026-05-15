import { describe, it, expect, beforeEach } from "vitest";
import { useUiPrefs } from "./uiPrefs";

describe("useUiPrefs", () => {
  beforeEach(() => useUiPrefs.setState({ theme: "light", searchOpen: false }));

  it("default theme is light", () => {
    expect(useUiPrefs.getState().theme).toBe("light");
  });

  it("setTheme updates the theme", () => {
    useUiPrefs.getState().setTheme("dark");
    expect(useUiPrefs.getState().theme).toBe("dark");
  });

  it("setTheme accepts system", () => {
    useUiPrefs.getState().setTheme("system");
    expect(useUiPrefs.getState().theme).toBe("system");
  });

  it("default searchOpen is false", () => {
    expect(useUiPrefs.getState().searchOpen).toBe(false);
  });

  it("setSearchOpen toggles the value", () => {
    useUiPrefs.getState().setSearchOpen(true);
    expect(useUiPrefs.getState().searchOpen).toBe(true);
    useUiPrefs.getState().setSearchOpen(false);
    expect(useUiPrefs.getState().searchOpen).toBe(false);
  });
});
