import { lazy, Suspense } from 'react'
import { Routes, Route, useLocation, Navigate } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import BottomNav from './components/BottomNav.jsx'
import { Skeleton } from './components/Skeleton.jsx'

// Route-level code splitting: each screen is its own async chunk, so the
// chart library (lightweight-charts) only loads when Analysis is visited.
const Home = lazy(() => import('./screens/Home.jsx'))
const Analysis = lazy(() => import('./screens/Analysis.jsx'))
const AIOutlook = lazy(() => import('./screens/AIOutlook.jsx'))
const Settings = lazy(() => import('./screens/Settings.jsx'))

function RouteFallback() {
  return (
    <div className="space-y-3 px-4 pt-5">
      <Skeleton className="h-7 w-1/3" />
      <Skeleton className="h-24 w-full rounded-2xl" />
      <Skeleton className="h-24 w-full rounded-2xl" />
    </div>
  )
}

export default function App() {
  const location = useLocation()

  return (
    // Centered device frame on wide screens; full-bleed on mobile.
    <div className="flex h-full justify-center bg-backdrop sm:py-6">
      <div className="relative flex h-full w-full max-w-md flex-col overflow-hidden bg-bg sm:h-[860px] sm:max-h-full sm:rounded-[2.25rem] sm:border sm:border-line sm:shadow-frame sm:ring-1 sm:ring-black/5">
        <main className="no-scrollbar flex-1 overflow-y-auto safe-bottom">
          <AnimatePresence mode="wait">
            <Suspense fallback={<RouteFallback />}>
              <Routes location={location} key={location.pathname}>
                <Route path="/" element={<Home />} />
                <Route path="/analysis" element={<Analysis />} />
                <Route path="/outlook" element={<AIOutlook />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Suspense>
          </AnimatePresence>
        </main>
        <BottomNav />
      </div>
    </div>
  )
}
