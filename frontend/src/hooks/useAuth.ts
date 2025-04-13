// トークンやログイン状態の管理
import { useEffect, useState } from 'react'

export const useAuth = () => {
  const [token, setToken] = useState<string | null>(null)

  useEffect(() => {
    const storedToken = localStorage.getItem('token')
    setToken(storedToken)
  }, [])
    
  const isAuthenticated = !!token
  
  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
  }

  return {
    token,
    isAuthenticated,
    logout,
  }
}