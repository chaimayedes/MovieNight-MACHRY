import { useEffect, useState } from 'react'
import { api } from '../api'
import MovieCard from '../components/MovieCard'
import Loader from '../components/Loader'

export default function Catalog() {
  const [data,    setData]    = useState({ total_results: 0, data: [] })
  const [page,    setPage]    = useState(1)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.catalog(page, 20)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [page])

  return (
    <div>
      <div className="flex items-end justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">Catalogue</h1>
          {data.total_results > 0 && (
            <p className="text-gray-500 text-sm mt-1">
              {data.total_results.toLocaleString()} films disponibles
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 rounded-lg bg-gray-900 border border-gray-800 text-white text-sm
              hover:border-gray-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            ← Précédent
          </button>
          <span className="px-3 py-2 text-gray-500 text-sm tabular-nums">Page {page}</span>
          <button
            onClick={() => setPage((p) => p + 1)}
            className="px-4 py-2 rounded-lg bg-gray-900 border border-gray-800 text-white text-sm
              hover:border-gray-600 transition-colors"
          >
            Suivant →
          </button>
        </div>
      </div>

      {loading ? (
        <Loader />
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {data.data?.map((movie) => (
            <MovieCard key={movie.id} movie={movie} />
          ))}
        </div>
      )}
    </div>
  )
}
