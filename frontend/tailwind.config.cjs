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
          bg: '#10152F',
          titlebar: '#4C6FF6',
          titlebarLight: '#6B8AFF',
          content: '#1A1F3A',
          border: '#3B4A6B',
          text: '#E8EAEF',
          textMuted: '#9CA3AF',
        },
      },
    },
  },
  plugins: [],
}
