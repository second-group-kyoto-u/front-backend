import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    console.log('🔐 ProtectedRoute - 認証確認中...')
    return <div>認証確認中...</div>
  }

  if (!isAuthenticated) {
    console.warn(`🔐 ProtectedRoute - 未認証。リダイレクト: ${location.pathname} → /login`)
    return <Navigate to="/login" replace />
  }

  console.log(`🔐 ProtectedRoute - 認証済。表示許可: ${location.pathname}`)
  return children
}
