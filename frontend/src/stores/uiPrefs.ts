import { create } from "zustand";

type Theme = "light" | "dark" | "system";

interface UiPrefsState {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  searchOpen: boolean;
  setSearchOpen: (v: boolean) => void;
}

export const useUiPrefs = create<UiPrefsState>()((set) => ({
  theme: "light",
  setTheme: (theme) => set({ theme }),
  searchOpen: false,
  setSearchOpen: (searchOpen) => set({ searchOpen }),
}));
