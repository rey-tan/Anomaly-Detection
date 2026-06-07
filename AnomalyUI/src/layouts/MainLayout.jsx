import React from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import NotificationsDropdown from '../components/NotificationsDropdown'
import FavoritesPanel from '../components/FavoritesPanel'
import NavButton from '../components/ui/NavButton'

const NAV_ITEMS = [
  { id: 'dashboard', path: '/dashboard', label: 'Dashboard', description: 'Overview' },
  { id: 'analysis', path: '/analysis', label: 'Analysis', description: 'Run model' },
  { id: 'activity', path: '/activity', label: 'Activity', description: 'Audit log' },
  { id: 'results', path: '/results', label: 'Results', description: 'Charts & metrics' },
  { id: 'data', path: '/data', label: 'Data', description: 'Data ' },
  { id: 'users', path: '/users', label: 'Users', description: 'User management' },
]

export default function MainLayout({
  user,
  token,
  results,
  selectedAnalysis,
  setResults,
  setSelectedAnalysis,
  onLogout,
  onOpenNotifications,
  handleOpenLastRun,
  handleSelectAnalysis,
  setActivityUser,
}) {
  const location = useLocation()
  const navigate = useNavigate()
  const latestRun = selectedAnalysis || {}
  const latestStock = latestRun?.stock || latestRun?.symbol
  const latestTimeframe = latestRun?.timeframe
  const latestStart = latestRun?.start_date || latestRun?.startDate
  const latestEnd = latestRun?.end_date || latestRun?.endDate
  const latestMode = latestRun?.mode
  const latestWindow = latestStart && latestEnd ? `${latestStart} – ${latestEnd}` : null

  const navItems = NAV_ITEMS.filter(
    (item) => item.id === 'dashboard' || item.id === 'analysis' || item.id === 'results' || user?.role === 'admin'
  )

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-copy">
          <p className="eyebrow">Anomaly Engine</p>
          <h1>Detect hidden market risk with precision.</h1>
          <p className="topbar-subtitle">
            Analyze your data for unusual patterns and potential risks.
          </p>
        </div>
        <div className="topbar-actions">
          <NotificationsDropdown token={token} onOpenAll={onOpenNotifications} onSelectAnalysis={handleSelectAnalysis} />
          <div className="user-chip">
            <div>
              <span>Signed in as</span>
              <strong>{user?.username || 'Guest'}</strong>
            </div>
            <button className="text-button" onClick={onLogout}>
              Sign out
            </button>
          </div>
        </div>
      </header>

      <section className="workspace-grid">
        <aside className="side-rail">
          <div className="side-rail-card">
            <p className="eyebrow">Workspace</p>
            <h2>Pages</h2>
          </div>

          <nav className="nav-stack" aria-label="Primary">
            {navItems.map((item) => (
              <NavButton
                key={item.id}
                item={item}
                active={location.pathname.startsWith(item.path)}
                badge={item.id === 'results' && results ? 'Live' : null}
              />
            ))}
          </nav>

          

          <button
            className="side-rail-card side-rail-footer side-rail-action"
            type="button"
            onClick={handleOpenLastRun}
            disabled={!selectedAnalysis}
            aria-label="Open the latest saved analysis"
          >
            <span>Last analysis</span>
            <h3>{latestStock || 'No analysis yet'}</h3>
            { latestRun ? (
              <div className="mt-5">
                <div>{latestTimeframe}</div> • <div>{latestWindow}</div>
              </div>
            ) : (
              <div className="mt-5">Run an analysis to see details here</div>
            )}
          </button>
        </aside>

        <main className="page-stage">
          <Outlet />
        </main>
      </section>
    </div>
  )
}
