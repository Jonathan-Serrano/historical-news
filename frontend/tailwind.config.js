/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        body: "var(--bg-body)",
        "text-primary": "var(--text-primary)",
        "text-secondary": "var(--text-secondary)",
        card: "var(--bg-card)",
        border: "var(--border-color)",
      },
    },
  },
  plugins: [],
};
