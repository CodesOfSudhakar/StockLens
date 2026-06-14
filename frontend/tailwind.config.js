/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Brand + semantic colours are fixed (read well on light & dark).
        primary: '#4F46E5', // iris indigo
        'primary-deep': '#3730A3',
        accent: '#9333EA', // violet
        bullish: '#10B981',
        bearish: '#F43F5E',
        neutral: '#F59E0B',
        // Neutrals are CSS-variable driven so they flip in dark mode.
        // Channels are space-separated RGB so Tailwind alpha (`/10`) still works.
        bg: 'rgb(var(--bg) / <alpha-value>)',
        backdrop: 'rgb(var(--backdrop) / <alpha-value>)',
        surface: 'rgb(var(--surface) / <alpha-value>)',
        ink: 'rgb(var(--ink) / <alpha-value>)',
        'ink-soft': 'rgb(var(--ink-soft) / <alpha-value>)',
        muted: 'rgb(var(--muted) / <alpha-value>)',
        line: 'rgb(var(--line) / <alpha-value>)',
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '0.875rem' }],
      },
      backgroundImage: {
        'gloss-primary':
          'linear-gradient(145deg, #6366F1 0%, #4F46E5 52%, #4338CA 100%)',
        'gloss-accent':
          'linear-gradient(145deg, #A855F7 0%, #9333EA 55%, #7E22CE 100%)',
      },
      boxShadow: {
        card: '0 1px 2px rgba(15,15,30,0.05), 0 6px 16px -8px rgba(79,70,229,0.14)',
        gloss:
          'inset 0 1px 0 rgba(255,255,255,0.35), 0 6px 18px -6px rgba(79,70,229,0.45)',
        frame: '0 24px 60px -20px rgba(10,10,20,0.45)',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      animation: {
        shimmer: 'shimmer 1.4s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
