/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        "background": "#0e150e",
        "primary": "#53e076",
        "primary-container": "#1db954",
        "on-primary-container": "#004118",
        "surface": "#0e150e",
        "surface-container": "#1a211a",
        "surface-variant": "#2f372e",
        "outline": "#869585",
        "on-surface-variant": "#bccbb9",
        "on-background": "#dde5d9",
        "tertiary-container": "#ff767b",
      },
      spacing: {
        "xs": "4px",
        "sm": "12px",
        "md": "24px",
        "lg": "40px",
        "xl": "64px",
        "gutter": "24px",
        "margin": "32px",
      },
      fontFamily: {
        "sans": ["Inter", "sans-serif"],
        "display": ["Spline Sans", "sans-serif"],
      },
      fontSize: {
        "label-bold": ["12px", { lineHeight: "1", letterSpacing: "0.05em", fontWeight: "700" }],
        "data-display": ["40px", { lineHeight: "1", fontWeight: "700" }],
        "headline-xl": ["48px", { lineHeight: "1.2", letterSpacing: "-0.02em", fontWeight: "700" }],
      },
      borderRadius: {
        "lg": "0.5rem",
        "xl": "0.75rem",
        "2xl": "1rem",
        "3xl": "1.5rem",
      }
    },
  },
  plugins: [],
}
