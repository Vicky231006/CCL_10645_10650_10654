/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ivory: {
          50: "#FDFCF9",
          100: "#F9F7F1",
          200: "#F2EFE6",
          300: "#E7E3D6",
        },
        ink: {
          DEFAULT: "#23211C",
          soft: "#3A3833",
          muted: "#6B675E",
          faint: "#9A958A",
        },
        stone: {
          100: "#EDEAE1",
          200: "#DDD9CE",
          300: "#C7C2B5",
        },
        forest: {
          DEFAULT: "#2E4A3D",
          dark: "#243A30",
          light: "#3E5F4E",
          tint: "#E8EFEA",
        },
        clay: {
          DEFAULT: "#8C4A31",
          dark: "#6E3722",
          tint: "#F4E9E4",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
        serif: ["'Source Serif 4'", "Georgia", "Cambria", "serif"],
      },
      boxShadow: {
        soft: "0 1px 2px rgba(35,33,28,0.04), 0 2px 8px rgba(35,33,28,0.05)",
        raised: "0 2px 4px rgba(35,33,28,0.06), 0 12px 24px -8px rgba(35,33,28,0.12)",
      },
      borderRadius: {
        md: "0.5rem",
        lg: "0.75rem",
      },
      maxWidth: {
        prose: "68ch",
      },
    },
  },
  plugins: [],
};
