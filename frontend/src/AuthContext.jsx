import { createContext, useContext, useState } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('mn_token'))
  const [user,  setUser]  = useState(() => {
    const stored = localStorage.getItem('mn_user')
    return stored ? JSON.parse(stored) : null
  })

  const saveAuth = (newToken, newUser) => {
    localStorage.setItem('mn_token', newToken)
    localStorage.setItem('mn_user', JSON.stringify(newUser))
    setToken(newToken)
    setUser(newUser)
  }

  const logout = () => {
    localStorage.removeItem('mn_token')
    localStorage.removeItem('mn_user')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ token, user, saveAuth, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
