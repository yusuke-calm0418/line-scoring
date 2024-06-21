/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './public/login.html',
    './public/index.html',
    './public/register.html',
    './public/dashboard.html',
    './public/user_info.html',
    './public/score_settings.html',
    './public/status_settings.html',
  ],
  theme: {
    extend: {
      fontFamily: {
        nunito: ['Nunito', 'sans-serif'],
      },
      colors: {
        primary: '#605BFF',
        second: 'rgba(172, 169, 255, 0.1)',
        bg: '#F7F7F8',
        textmain: '#101059',
        status1: '#B7CFFE',
        status2: '#9A9AA9',
        status3: '#FFC7D4',
        status4: '#D3D3D3',
        status5: '#98FB98',
        status6: '#FFFFE0',
        score1: '#B7CFFE',
        score2: '#FED5B7',
        white: '#FFFFFF',
      },
    },
  },
  plugins: [],
}
