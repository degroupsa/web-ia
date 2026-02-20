/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    // Rutas corregidas (sin "src")
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    
    // Rutas de respaldo por si acaso
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        kortexa: {
          main: "#0E1117",
          sidebar: "#262730",
          orange: "#FF5F1F",
          yellow: "#FFAA00"
        }
      }
    },
  },
  plugins: [],
}