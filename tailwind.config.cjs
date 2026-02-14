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
        // Decorative only: page headers, high-level section titles. Not for form labels or body text.
        rochester: ['Rochester', 'cursive'],
      },
      colors: {
        valentine: {
          50: '#fdf2f8',
          100: '#fce7f3',
          200: '#fbcfe8',
          300: '#f9a8d4',
          400: '#f472b6',
          500: '#ec4899',
          600: '#db2777',
          700: '#be185d',
          800: '#9d174d',
          900: '#831843',
        },
      },
    },
  },
  plugins: [],
}
