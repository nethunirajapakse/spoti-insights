import { create } from "zustand";

/**
 * Demo mode lets anyone explore the full app with built-in sample data, no
 * Spotify login required. Spotify limits apps in development mode to an
 * allowlist of accounts, so most visitors (recruiters, reviewers) can't sign in.
 *
 * The flag lives in sessionStorage so it survives a page refresh but ends when
 * the tab is closed. It is deliberately NOT localStorage: a stale flag should
 * never hide a real account's data on a later visit.
 */
const STORAGE_KEY = "spoti-insights:demo";

const readFlag = (): boolean => {
  try {
    return globalThis.sessionStorage.getItem(STORAGE_KEY) === "1";
  } catch {
    return false;
  }
};

const writeFlag = (on: boolean) => {
  try {
    if (on) {
      globalThis.sessionStorage.setItem(STORAGE_KEY, "1");
    } else {
      globalThis.sessionStorage.removeItem(STORAGE_KEY);
    }
  } catch {
    // Storage can be blocked (private mode, strict settings); the in-memory
    // flag below still works for the current page load.
  }
};

interface DemoState {
  isDemo: boolean;
  enable: () => void;
  disable: () => void;
}

export const useDemoStore = create<DemoState>((set) => ({
  isDemo: readFlag(),
  enable: () => {
    writeFlag(true);
    set({ isDemo: true });
  },
  disable: () => {
    writeFlag(false);
    set({ isDemo: false });
  },
}));

/** Non-hook accessor for plain functions (the API layer). */
export const isDemoMode = (): boolean => useDemoStore.getState().isDemo;
