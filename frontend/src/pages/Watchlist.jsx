import { useEffect, useState } from 'react'
import { api } from '../api'
import MovieCard from '../components/MovieCard'
import Loader from '../components/Loader'

export default function Watchlist() {
  const [movies,  setMovies]  = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.watchlist()
      .then(setMovies)
      .catch(() => setMovies([]))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">Ma Watchlist</h1>
        <p className="text-gray-500 text-sm mt-1">Films sauvegardés — utilisateur #1</p>
      </div>

      {loading ? (
        <Loader />
      ) : movies.length === 0 ? (
        <div className="text-center py-24">
          <p className="text-gray-600 text-lg">Ta watchlist est vide.</p>
          <p className="text-gray-700 text-sm mt-2">
            Ajoute des films depuis la page de détail.
          </p>
        </div>
      ) : (
        <>
          <p className="text-gray-500 text-sm mb-6">
            {movies.length} film{movies.length > 1 ? 's' : ''}
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {movies.map((movie) => (
              <MovieCard key={movie.id} movie={movie} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
