import { useState } from 'react'
import { api } from '../api'
import MovieCard from '../components/MovieCard'
import Loader from '../components/Loader'

export default function Search() {
  const [query,    setQuery]    = useState('')
  const [results,  setResults]  = useState([])
  const [loading,  setLoading]  = useState(false)
  const [searched, setSearched] = useState(false)

  const search = async () => {
    if (!query.trim()) return
    setLoading(true)
    setSearched(false)
    try {
      const data = await api.search(query.trim())
      setResults(data)
    } catch {
      setResults([])
    } finally {
      setLoading(false)
      setSearched(true)
    }
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-white mb-8">Recherche</h1>

      <div className="flex gap-3 mb-10">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && search()}
          placeholder="Titre d'un film..."
          className="flex-1 bg-gray-900 border border-gray-800 text-white placeholder-gray-600
            rounded-xl px-5 py-4 text-base focus:outline-none focus:border-amber-500 transition-colors"
        />
        <button
          onClick={search}
          disabled={!query.trim() || loading}
          className="px-8 py-4 bg-amber-500 hover:bg-amber-400 text-black font-semibold rounded-xl
            transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {loading ? '...' : 'Chercher'}
        </button>
      </div>

      {loading && <Loader />}

      {searched && !loading && (
        results.length === 0 ? (
          <p className="text-gray-500 text-center py-16">
            Aucun film trouvé pour «&nbsp;{query}&nbsp;»
          </p>
        ) : (
          <>
            <p className="text-gray-500 text-sm mb-6">
              {results.length} résultat{results.length > 1 ? 's' : ''}
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
              {results.map((movie) => (
                <MovieCard key={movie.id} movie={movie} />
              ))}
            </div>
          </>
        )
      )}
    </div>
  )
}
