import { NavLink } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useResolvedTheme } from '../store/useTheme.js'

const ICONS = {
  home: (
    <path d="M3 10.5 12 3l9 7.5M5 9.5V20a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1V9.5" />
  ),
  analysis: (
    <path d="M4 19V5m0 14h16M8 16V9m4 7v-5m4 5V7" />
  ),
  outlook: (
    <path d="M12 3a6 6 0 0 0-4 10.5c.6.6 1 1.3 1 2.1V17h6v-1.4c0-.8.4-1.5 1-2.1A6 6 0 0 0 12 3ZM9.5 20h5M10 22h4" />
  ),
  settings: (
    <>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-1.8-.3 1.6 1.6 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.6 1.6 0 0 0-1-1.5 1.6 1.6 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0 .3-1.8 1.6 1.6 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.6 1.6 0 0 0 1.5-1 1.6 1.6 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.6 1.6 0 0 0 1.8.3H9a1.6 1.6 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.6 1.6 0 0 0 1 1.5 1.6 1.6 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0-.3 1.8V9a1.6 1.6 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1Z" />
    </>
  ),
}

const TABS = [
  { to: '/', label: 'Home', icon: 'home' },
  { to: '/analysis', label: 'Analysis', icon: 'analysis' },
  { to: '/outlook', label: 'AI', icon: 'outlook' },
  { to: '/settings', label: 'Settings', icon: 'settings' },
]

export default function BottomNav() {
  const theme = useResolvedTheme()
  const activeStroke = theme === 'dark' ? '#818CF8' : '#4F46E5'
  const idleStroke = theme === 'dark' ? '#8488A0' : '#9296AD'
  return (
    <nav className="absolute inset-x-0 bottom-0 z-30 border-t border-line bg-surface/80 backdrop-blur-xl">
      <div
        className="flex items-stretch justify-around"
        style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
      >
        {TABS.map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            end={tab.to === '/'}
            className="relative flex flex-1 flex-col items-center gap-0.5 py-2.5"
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <motion.span
                    layoutId="navpill"
                    className="absolute -top-px h-0.5 w-8 rounded-full bg-gloss-primary"
                  />
                )}
                <svg
                  viewBox="0 0 24 24"
                  className="h-[22px] w-[22px]"
                  fill="none"
                  stroke={isActive ? activeStroke : idleStroke}
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  {ICONS[tab.icon]}
                </svg>
                <span
                  className={`text-2xs font-semibold ${
                    isActive ? 'text-primary' : 'text-muted'
                  }`}
                >
                  {tab.label}
                </span>
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
