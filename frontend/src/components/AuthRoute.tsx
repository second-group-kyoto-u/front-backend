// AuthRoute.tsx
import React, { useEffect } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export const AuthRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()
  
  // デバッグログ
  useEffect(() => {
    console.log('🔓 AuthRoute - マウント時の状態:');
    console.log('  - 認証状態:', isAuthenticated);
    console.log('  - 読み込み中:', isLoading);
    console.log('  - 現在のパス:', location.pathname);
    console.log('  - リダイレクト元:', location.state?.from || 'なし');
  }, [isAuthenticated, isLoading, location]);

  if (isLoading) {
    console.log('🔓 AuthRoute - 認証確認中...');
    return <div>確認中...</div>
  }

  // すでに認証済みの場合
  if (isAuthenticated) {
    console.log('🔓 AuthRoute - 認証済みユーザー。リダイレクト処理を決定:');
    
    // locationのstateを確認
    const from = location.state?.from;
    
    if (from === '/event/create') {
      // イベント作成ページへのアクセスだった場合
      console.log('  - イベント作成ページへリダイレクト:', from);
      return <Navigate to={from} replace />
    }
    
    // それ以外はマイページへ
    console.log('  - マイページへリダイレクト');
    return <Navigate to="/mypage" replace />
  }

  console.log('🔓 AuthRoute - 未認証ユーザー。ログイン画面を表示');
  return children
}
