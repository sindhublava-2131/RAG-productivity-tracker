/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cozy: {
          bg: "#FAF6F0",
          card: "#FFFFFF",
          pink: "#FFDFE5",
          rose: "#FF8DA1",
          mint: "#D1FAE5",
          sage: "#10B981",
          yellow: "#FEF3C7",
          amber: "#F59E0B",
          lavender: "#EDE9FE",
          purple: "#8B5CF6",
          blue: "#E0F2FE",
          sky: "#0284C7",
          text: "#4A3E3D",
          muted: "#9CA3AF"
        }
      },
      borderRadius: {
        '4xl': '2.5rem',
        '5xl': '3rem'
      },
      boxShadow: {
        'cozy': '0 8px 30px rgba(255, 183, 197, 0.18)',
        'cozy-hover': '0 12px 35px rgba(255, 141, 161, 0.25)',
        'soft': '0 4px 20px rgba(0, 0, 0, 0.04)'
      },
      fontFamily: {
        sans: ['Fredoka', 'Quicksand', 'Outfit', 'Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
