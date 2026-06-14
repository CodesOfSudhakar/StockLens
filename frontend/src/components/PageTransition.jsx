import { motion } from 'framer-motion'

const variants = {
  initial: { opacity: 0, y: 12 },
  enter: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
}

export default function PageTransition({ title, subtitle, action, children }) {
  return (
    <motion.div
      variants={variants}
      initial="initial"
      animate="enter"
      exit="exit"
      transition={{ duration: 0.25, ease: 'easeOut' }}
      className="px-4 pt-4"
    >
      {(title || action) && (
        <header className="mb-4 flex items-start justify-between">
          <div>
            {title && (
              <h1 className="text-base font-bold tracking-tight text-ink">{title}</h1>
            )}
            {subtitle && (
              <p className="mt-0.5 text-2xs font-medium text-muted">{subtitle}</p>
            )}
          </div>
          {action}
        </header>
      )}
      {children}
    </motion.div>
  )
}
