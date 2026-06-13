/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: "#050505",
          card: "#0d0d0d",
          border: "#1f1f1f",
          accent: "#00ff9d", // Vert néon Cyber
          text: "#e0e0e0"
        }
      }
    },
  },
  plugins: [],
}
