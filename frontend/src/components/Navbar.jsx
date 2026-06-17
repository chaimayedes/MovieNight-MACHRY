import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'

const LINKS = [
  { to: '/',          label: 'Soirée' },
  { to: '/catalog',   label: 'Catalogue' },
  { to: '/search',    label: 'Recherche' },
  { to: '/watchlist', label: 'Watchlist' },
]

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

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

        <div className="flex items-center gap-3">
          {user ? (
            <>
              <span className="text-gray-400 text-sm hidden sm:block">
                {user.username}
              </span>
              <button
                onClick={handleLogout}
                className="px-3 py-1.5 text-sm text-gray-400 hover:text-white border border-gray-700
                  hover:border-gray-500 rounded-lg transition-colors"
              >
                Déconnexion
              </button>
            </>
          ) : (
            <>
              <NavLink
                to="/login"
                className="px-3 py-1.5 text-sm text-gray-400 hover:text-white transition-colors"
              >
                Connexion
              </NavLink>
              <NavLink
                to="/register"
                className="px-3 py-1.5 text-sm bg-amber-500 hover:bg-amber-400 text-black
                  font-semibold rounded-lg transition-colors"
              >
                S'inscrire
              </NavLink>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
