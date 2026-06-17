import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './AuthContext'
import Navbar from './components/Navbar'
import Recommend from './pages/Recommend'
import Catalog from './pages/Catalog'
import Search from './pages/Search'
import MovieDetail from './pages/MovieDetail'
import Watchlist from './pages/Watchlist'
import Login from './pages/Login'
import Register from './pages/Register'

function ProtectedRoute({ children }) {
  const { token } = useAuth()
  return token ? children : <Navigate to="/login" replace />
}

function AppRoutes() {
  return (
    <>
      <Navbar />
      <main className="max-w-7xl mx-auto px-6 py-10">
        <Routes>
          <Route path="/"           element={<Recommend />} />
          <Route path="/catalog"    element={<Catalog />} />
          <Route path="/search"     element={<Search />} />
          <Route path="/movies/:id" element={<MovieDetail />} />
          <Route path="/login"      element={<Login />} />
          <Route path="/register"   element={<Register />} />
          <Route
            path="/watchlist"
            element={
              <ProtectedRoute>
                <Watchlist />
              </ProtectedRoute>
            }
          />
        </Routes>
      </main>
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
