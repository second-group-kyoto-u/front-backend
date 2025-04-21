// AuthRoute.tsx
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export const AuthRoute = ({ children }: { children: JSX.Element }) => {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) return <div>確認中...</div>

  // 👇 無限ループ防止のために、location.pathname === '/login' ではなく、単に isAuthenticated を見る
  if (isAuthenticated) {
    return <Navigate to="/mypage" replace />
  }

  return children
}
