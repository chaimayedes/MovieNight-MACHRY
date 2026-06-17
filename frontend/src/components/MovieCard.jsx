import { useNavigate } from 'react-router-dom'

const POSTER = 'https://image.tmdb.org/t/p/w500'

export default function MovieCard({ movie, badge }) {
  const navigate = useNavigate()

  return (
    <div
      onClick={() => navigate(`/movies/${movie.id}`)}
      className="group cursor-pointer bg-gray-900 rounded-xl overflow-hidden border border-gray-800
        hover:border-amber-500/30 hover:scale-[1.03] hover:shadow-2xl hover:shadow-black/60
        transition-all duration-300"
    >
      <div className="relative aspect-[2/3] overflow-hidden">
        {movie.poster_path ? (
          <img
            src={`${POSTER}${movie.poster_path}`}
            alt={movie.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          />
        ) : (
          <div className="w-full h-full bg-gray-800 flex items-center justify-center p-4">
            <span className="text-gray-600 text-xs text-center">{movie.title}</span>
          </div>
        )}
        {badge && (
          <span className="absolute top-2 left-2 bg-amber-500 text-black text-xs font-bold px-2 py-1 rounded-md">
            {badge}
          </span>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent
          opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-4">
          <p className="text-gray-300 text-xs">Voir les détails →</p>
        </div>
      </div>
      <div className="p-3">
        <h3 className="text-white font-semibold text-sm leading-snug line-clamp-2">{movie.title}</h3>
        {movie.release_date && (
          <p className="text-gray-600 text-xs mt-1">{movie.release_date.slice(0, 4)}</p>
        )}
      </div>
    </div>
  )
}
