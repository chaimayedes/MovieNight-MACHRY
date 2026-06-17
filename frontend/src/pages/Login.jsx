import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../AuthContext'

export default function Login() {
  const [form,  setForm]  = useState({ username: '', password: '' })
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const { saveAuth } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const resp = await api.login(form.username, form.password)
      saveAuth(resp.token, resp.user)
      navigate('/')
    } catch {
      setError('Identifiants incorrects.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-sm mx-auto mt-20">
      <h1 className="text-3xl font-bold text-white mb-2">Connexion</h1>
      <p className="text-gray-500 text-sm mb-8">Retrouve ta watchlist et tes notes.</p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="text"
          placeholder="Nom d'utilisateur"
          value={form.username}
          onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
          className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-xl text-white
            placeholder-gray-600 focus:outline-none focus:border-amber-500 transition-colors"
          required
        />
        <input
          type="password"
          placeholder="Mot de passe"
          value={form.password}
          onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
          className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-xl text-white
            placeholder-gray-600 focus:outline-none focus:border-amber-500 transition-colors"
          required
        />
        {error && <p className="text-red-400 text-sm">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 bg-amber-500 hover:bg-amber-400 disabled:opacity-50
            text-black font-bold rounded-xl transition-colors"
        >
          {loading ? 'Connexion…' : 'Se connecter'}
        </button>
      </form>

      <p className="text-gray-500 text-sm mt-6 text-center">
        Pas encore de compte ?{' '}
        <Link to="/register" className="text-amber-500 hover:underline">
          S'inscrire
        </Link>
      </p>
    </div>
  )
}
