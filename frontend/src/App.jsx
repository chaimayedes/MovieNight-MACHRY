import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Recommend from './pages/Recommend'
import Catalog from './pages/Catalog'
import Search from './pages/Search'
import MovieDetail from './pages/MovieDetail'
import Watchlist from './pages/Watchlist'

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <main className="max-w-7xl mx-auto px-6 py-10">
        <Routes>
          <Route path="/"           element={<Recommend />} />
          <Route path="/catalog"    element={<Catalog />} />
          <Route path="/search"     element={<Search />} />
          <Route path="/movies/:id" element={<MovieDetail />} />
          <Route path="/watchlist"  element={<Watchlist />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
