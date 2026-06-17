import { useState } from 'react'
import { api } from '../api'
import MovieCard from '../components/MovieCard'
import Loader from '../components/Loader'

const MOODS = [
  { id: 'chill',  label: 'Chill',   desc: 'Détente & ambiance',      bar: 'from-blue-500 to-cyan-400' },
  { id: 'scary',  label: 'Frisson', desc: 'Horreur & suspense',       bar: 'from-purple-600 to-red-500' },
  { id: 'laugh',  label: 'Rire',    desc: 'Comédie & bonne humeur',   bar: 'from-yellow-400 to-orange-400' },
  { id: 'cry',    label: 'Émotion', desc: 'Drame & larmes',           bar: 'from-blue-600 to-indigo-500' },
  { id: 'action', label: 'Action',  desc: 'Adrénaline & spectacle',   bar: 'from-red-500 to-orange-500' },
]

const GROUPS = [
  { id: 'solo',    label: 'Solo',    desc: 'Juste toi' },
  { id: 'couple',  label: 'Couple',  desc: 'À deux' },
  { id: 'friends', label: 'Amis',    desc: 'Entre potes' },
  { id: 'family',  label: 'Famille', desc: 'Pour tous' },
]

const BADGES = ['#1', '#2', '#3']

export default function Recommend() {
  const [mood,    setMood]    = useState(null)
  const [group,   setGroup]   = useState(null)
  const [movies,  setMovies]  = useState([])
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState(null)
  const [done,    setDone]    = useState(false)

  const submit = async () => {
    if (!mood || !group) return
    setLoading(true)
    setError(null)
    setDone(false)
    try {
      const data = await api.recommend(mood, group)
      setMovies(data)
      setDone(true)
    } catch {
      setError('Impossible de charger les recommandations. Le serveur est-il lancé ?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="text-center mb-14">
        <h1 className="text-5xl font-extrabold text-white mb-4 tracking-tight">
          Quelle soirée ce soir ?
        </h1>
        <p className="text-gray-400 text-lg">
          Choisis ton humeur et ton groupe — on s'occupe du reste.
        </p>
      </div>

      <section className="mb-10">
        <p className="text-xs font-semibold uppercase tracking-widest text-amber-500 mb-4">
          Ton humeur
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {MOODS.map((m) => (
            <button
              key={m.id}
              onClick={() => setMood(m.id)}
              className={`p-5 rounded-xl border-2 text-left transition-all duration-200
                ${mood === m.id
                  ? 'border-amber-500 bg-amber-500/10 shadow-lg shadow-amber-500/10 scale-[1.03]'
                  : 'border-gray-800 bg-gray-900 hover:border-gray-700'
                }`}
            >
              <div className={`h-1 w-10 rounded-full bg-gradient-to-r ${m.bar} mb-4`} />
              <p className="text-white font-semibold">{m.label}</p>
              <p className="text-gray-500 text-xs mt-1 leading-relaxed">{m.desc}</p>
            </button>
          ))}
        </div>
      </section>

      <section className="mb-12">
        <p className="text-xs font-semibold uppercase tracking-widest text-amber-500 mb-4">
          Avec qui ?
        </p>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {GROUPS.map((g) => (
            <button
              key={g.id}
              onClick={() => setGroup(g.id)}
              className={`p-5 rounded-xl border-2 text-left transition-all duration-200
                ${group === g.id
                  ? 'border-amber-500 bg-amber-500/10 shadow-lg shadow-amber-500/10 scale-[1.03]'
                  : 'border-gray-800 bg-gray-900 hover:border-gray-700'
                }`}
            >
              <p className="text-white font-semibold text-lg">{g.label}</p>
              <p className="text-gray-500 text-sm mt-1">{g.desc}</p>
            </button>
          ))}
        </div>
      </section>

      <div className="text-center mb-16">
        <button
          onClick={submit}
          disabled={!mood || !group || loading}
          className="px-12 py-4 bg-amber-500 hover:bg-amber-400 text-black font-bold text-lg rounded-xl
            transition-all duration-200 hover:scale-105 hover:shadow-xl hover:shadow-amber-500/25
            disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
        >
          {loading ? 'Recherche en cours...' : 'Trouver mes films'}
        </button>
      </div>

      {loading && <Loader />}

      {error && (
        <p className="text-center text-red-400 py-10">{error}</p>
      )}

      {done && !loading && (
        <section>
          <h2 className="text-2xl font-bold text-white mb-6">Top 3 pour ce soir</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {movies.map((movie, i) => (
              <MovieCard key={movie.id} movie={movie} badge={BADGES[i]} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
