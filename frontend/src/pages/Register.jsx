import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../AuthContext'

export default function Register() {
  const [form,    setForm]    = useState({ username: '', password: '', confirm: '' })
  const [error,   setError]   = useState(null)
  const [loading, setLoading] = useState(false)
  const { saveAuth } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    if (form.password !== form.confirm) {
      setError('Les mots de passe ne correspondent pas.')
      return
    }
    if (form.password.length < 6) {
      setError('Le mot de passe doit faire au moins 6 caractères.')
      return
    }

    setLoading(true)
    try {
      const resp = await api.register(form.username, form.password)
      saveAuth(resp.token, resp.user)
      navigate('/')
    } catch (err) {
      setError(err.message === 'Conflict' ? 'Ce nom d\'utilisateur est déjà pris.' : 'Erreur lors de l\'inscription.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-sm mx-auto mt-20">
      <h1 className="text-3xl font-bold text-white mb-2">Créer un compte</h1>
      <p className="text-gray-500 text-sm mb-8">Ta watchlist et tes notes rien qu'à toi.</p>

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
        <input
          type="password"
          placeholder="Confirmer le mot de passe"
          value={form.confirm}
          onChange={(e) => setForm((f) => ({ ...f, confirm: e.target.value }))}
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
          {loading ? 'Création…' : 'Créer mon compte'}
        </button>
      </form>

      <p className="text-gray-500 text-sm mt-6 text-center">
        Déjà un compte ?{' '}
        <Link to="/login" className="text-amber-500 hover:underline">
          Se connecter
        </Link>
      </p>
    </div>
  )
}
