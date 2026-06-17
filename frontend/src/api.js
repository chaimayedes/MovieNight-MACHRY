const BASE = '/api/v1'

const get = (url) =>
  fetch(url).then((r) => {
    if (!r.ok) throw new Error(r.statusText)
    return r.json()
  })

const post = (url, body) =>
  fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then((r) => {
    if (!r.ok) throw new Error(r.statusText)
    return r.json()
  })

export const api = {
  recommend:      (mood, group)      => get(`${BASE}/recommendation?mood=${mood}&group=${group}`),
  catalog:        (page = 1, limit = 20) => get(`${BASE}/movies?page=${page}&limit=${limit}`),
  movie:          (id)               => get(`${BASE}/movies/${id}`),
  search:         (query)            => get(`${BASE}/search?query=${encodeURIComponent(query)}`),
  rate:           (id, rating)       => post(`${BASE}/movies/${id}/rate`, { user_id: 1, rating }),
  watchlist:      ()                 => get(`${BASE}/user/1/watchlist`),
  addToWatchlist: (movieId)          => post(`${BASE}/user/1/watchlist`, { movie_id: movieId }),
}
