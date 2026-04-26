/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./templates/**/*.html'],
  theme: {
    extend: {
      colors: {
        navy: {
          50: '#eef2ff',
          100: '#dce6ff',
          200: '#b9ccff',
          600: '#1a38f5',
          700: '#1228e0',
          800: '#1122b8',
          900: '#0d1880',
          950: '#080e52',
        },
        gold: {
          300: '#fde68a',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
        },
      },
      fontFamily: {
        poppins: ['Poppins', 'sans-serif'],
        devanagari: ['Tiro Devanagari Hindi', 'serif'],
      },
    },
  },
  plugins: [],
};
