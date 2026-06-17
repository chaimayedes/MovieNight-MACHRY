import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api'
import Loader from '../components/Loader'
import StarRating from '../components/StarRating'

const POSTER = 'https://image.tmdb.org/t/p/w500'

export default function MovieDetail() {
  const { id }     = useParams()
  const navigate   = useNavigate()
  const [movie,    setMovie]    = useState(null)
  const [loading,  setLoading]  = useState(true)
  const [rated,    setRated]    = useState(false)
  const [watchMsg, setWatchMsg] = useState(null)

  useEffect(() => {
    api.movie(id)
      .then(setMovie)
      .catch(() => navigate('/'))
      .finally(() => setLoading(false))
  }, [id])

  const handleRate = async (stars) => {
    try {
      await api.rate(id, stars)
      setRated(true)
    } catch (e) {
      console.error(e)
    }
  }

  const handleWatchlist = async () => {
    try {
      await api.addToWatchlist(Number(id))
      setWatchMsg('Ajouté à ta watchlist !')
    } catch {
      setWatchMsg('Déjà dans ta watchlist.')
    }
    setTimeout(() => setWatchMsg(null), 3000)
  }

  if (loading) return <Loader />
  if (!movie)  return null

  return (
    <div>
      <button
        onClick={() => navigate(-1)}
        className="text-gray-500 hover:text-white text-sm mb-8 transition-colors"
      >
        ← Retour
      </button>

      <div className="flex flex-col md:flex-row gap-10">
        <div className="flex-shrink-0 w-full md:w-64">
          {movie.poster_path ? (
            <img
              src={`${POSTER}${movie.poster_path}`}
              alt={movie.title}
              className="w-full rounded-xl shadow-2xl shadow-black"
            />
          ) : (
            <div className="w-full aspect-[2/3] bg-gray-800 rounded-xl flex items-center justify-center">
              <span className="text-gray-600 text-sm">Pas d'affiche</span>
            </div>
          )}
        </div>

        <div className="flex-1 min-w-0">
          <h1 className="text-4xl font-extrabold text-white mb-3 leading-tight">
            {movie.title}
          </h1>

          <div className="flex flex-wrap items-center gap-3 mb-6 text-sm text-gray-400">
            {movie.release_date && <span>{movie.release_date.slice(0, 4)}</span>}
            {movie.duration > 0 && (
              <>
                <span className="text-gray-700">·</span>
                <span>{movie.duration} min</span>
              </>
            )}
          </div>

          {movie.genres?.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-6">
              {movie.genres.map((g) => (
                <span
                  key={g}
                  className="px-3 py-1 bg-gray-800 text-gray-300 text-xs rounded-full border border-gray-700"
                >
                  {g}
                </span>
              ))}
            </div>
          )}

          {movie.overview && (
            <p className="text-gray-300 leading-relaxed mb-8">{movie.overview}</p>
          )}

          {movie.casting?.length > 0 && (
            <div className="mb-8">
              <p className="text-xs font-semibold uppercase tracking-widest text-amber-500 mb-3">
                Casting
              </p>
              <div className="flex flex-wrap gap-2">
                {movie.casting.map((actor) => (
                  <span
                    key={actor}
                    className="px-3 py-1 bg-gray-900 border border-gray-800 text-gray-300 text-xs rounded-full"
                  >
                    {actor}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="mb-8">
            <p className="text-xs font-semibold uppercase tracking-widest text-amber-500 mb-3">
              {rated ? 'Note enregistrée' : 'Note ce film'}
            </p>
            <StarRating onRate={handleRate} submitted={rated} />
          </div>

          <div className="flex items-center gap-4 flex-wrap">
            <button
              onClick={handleWatchlist}
              className="px-6 py-3 bg-gray-900 hover:bg-gray-800 text-white text-sm font-medium
                rounded-xl transition-colors border border-gray-700 hover:border-amber-500/40"
            >
              + Ajouter à la watchlist
            </button>
            {watchMsg && (
              <span className="text-amber-500 text-sm">{watchMsg}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
