/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Confidence level colors (per D-06)
        confidence: {
          1: '#9E9E9E', // Unverified - gray
          2: '#FFC107', // Single Source - amber
          3: '#4CAF50', // Cross-Validated - green
          4: '#2196F3', // Human Verified - blue
        },
        // Freshness colors (per D-06)
        freshness: {
          0: '#4CAF50', // Level 0 - green (fresh)
          1: '#8BC34A',
          2: '#CDDC39',
          3: '#FFEB3B',
          4: '#FFC107',
          5: '#FF9800',
          6: '#FF5722',
          7: '#F44336',
          8: '#B71C1C', // Level 8 - dark red (stale)
        },
      },
    },
  },
}