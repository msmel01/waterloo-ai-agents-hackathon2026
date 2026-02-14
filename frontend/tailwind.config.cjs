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
        win: {
          bg: '#0D0118',
          titlebar: '#8301E1',
          titlebarLight: '#9B2EED',
          titlebarDark: '#5C01A3',
          content: '#1A1025',
          border: '#2D1B4E',
          borderLight: '#4A2D6B',
          text: '#E8EAEF',
          textMuted: '#9CA3AF',
        },
      },
    },
  },
  plugins: [],
}
