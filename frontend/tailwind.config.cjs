/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Tahoma', 'Verdana', 'Geneva', 'sans-serif'],
      },
      colors: {
        /* Palette: Bright Indigo, Lavender Purple, Orchid Mist, Pink Carnation, Desert Sand */
        palette: {
          indigo: '#2F3CD8',
          lavender: '#905ACA',
          orchid: '#C566C2',
          pink: '#F487B8',
          sand: '#F5E7F0',
        },
        win: {
          bg: '#1A1540',
          titlebar: '#905ACA',
          titlebarLight: '#C566C2',
          titlebarDark: '#2F3CD8',
          content: '#251D50',
          border: '#905ACA',
          borderLight: '#C566C2',
          text: '#F5E7F0',
          textMuted: '#C566C2',
        },
      },
    },
  },
  plugins: [],
}
