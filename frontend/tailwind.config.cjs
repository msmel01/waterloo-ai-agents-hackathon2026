/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Noto Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        rochester: ['Rochester', 'cursive'],
        pixel: ['VT323', 'monospace'],
      },
      colors: {
        y2k: {
          hotpink: '#ff1493',
          lime: '#39ff14',
          cyan: '#00ffff',
          purple: '#9d4edd',
          electric: '#7df9ff',
          magenta: '#ff00ff',
        },
      },
      boxShadow: {
        'neon-pink': '0 0 10px #ff1493, 0 0 20px #ff1493, 0 0 30px #ff1493',
        'neon-cyan': '0 0 10px #00ffff, 0 0 20px #00ffff, 0 0 30px #00ffff',
        'neon-lime': '0 0 10px #39ff14, 0 0 20px #39ff14',
      },
    },
  },
  plugins: [],
}
