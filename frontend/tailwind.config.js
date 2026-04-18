/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        slate: {
          950: '#030712',
        },
        aurora: {
          sky: '#0ea5e9',
          purple: '#8b5cf6',
          pink: '#ec4899',
        }
      },
      fontFamily: {
        inter: ['Inter', 'sans-serif'],
        outfit: ['Outfit', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      backgroundImage: {
        'gradient-aurora': 'linear-gradient(to right, #0ea5e9, #8b5cf6, #ec4899)',
      }
    },
  },
  plugins: [],
}
