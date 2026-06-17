import { NavLink } from 'react-router-dom'

const LINKS = [
  { to: '/',          label: 'Soirée' },
  { to: '/catalog',   label: 'Catalogue' },
  { to: '/search',    label: 'Recherche' },
  { to: '/watchlist', label: 'Watchlist' },
]

export default function Navbar() {
  return (
    <nav className="sticky top-0 z-50 border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <NavLink to="/" className="text-xl font-extrabold text-white tracking-tight">
          Movie<span className="text-amber-500">Night</span>
        </NavLink>
        <div className="flex items-center gap-1">
          {LINKS.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-150 ${
                  isActive
                    ? 'bg-amber-500/15 text-amber-500'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  )
}
