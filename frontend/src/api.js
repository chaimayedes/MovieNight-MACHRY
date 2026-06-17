const BASE = '/api/v1'

const authHeaders = () => {
  const token = localStorage.getItem('mn_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

const get = (url, auth = false) =>
  fetch(url, { headers: auth ? authHeaders() : {} }).then((r) => {
    if (!r.ok) throw new Error(r.statusText)
    return r.json()
  })

const post = (url, body, auth = false) =>
  fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(auth ? authHeaders() : {}) },
    body: JSON.stringify(body),
  }).then((r) => {
    if (!r.ok) throw new Error(r.statusText)
    return r.json()
  })

export const api = {
  // Auth
  register: (username, password) => post(`${BASE}/auth/register`, { username, password }),
  login:    (username, password) => post(`${BASE}/auth/login`,    { username, password }),

  // Public
  recommend: (mood, group)           => get(`${BASE}/recommendation?mood=${mood}&group=${group}`),
  catalog:   (page = 1, limit = 20)  => get(`${BASE}/movies?page=${page}&limit=${limit}`),
  movie:     (id)                    => get(`${BASE}/movies/${id}`),
  search:    (query)                 => get(`${BASE}/search?query=${encodeURIComponent(query)}`),

  // Protected (require JWT)
  rate:           (id, rating) => post(`${BASE}/movies/${id}/rate`, { rating }, true),
  watchlist:      ()           => get(`${BASE}/watchlist`, true),
  addToWatchlist: (movieId)    => post(`${BASE}/watchlist`, { movie_id: movieId }, true),
}
