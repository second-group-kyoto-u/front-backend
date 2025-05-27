import React, { useEffect } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  // デバッグ用ログ
  useEffect(() => {
    console.log('🔍 ProtectedRoute - マウント時の状態:');
    console.log('  - 認証状態:', isAuthenticated);
    console.log('  - 読み込み中:', isLoading);
    console.log('  - 現在のパス:', location.pathname);
    console.log('  - 完全なURL:', window.location.href);
  }, [isAuthenticated, isLoading, location]);

  if (isLoading) {
    console.log('🔐 ProtectedRoute - 認証確認中...')
    return <div>認証確認中...</div>
  }

  if (!isAuthenticated) {
    console.warn(`🔐 ProtectedRoute - 未認証。リダイレクト: ${location.pathname} → /login`)
    // デバッグ詳細を出力
    console.log(`  - 現在のURL: ${window.location.href}`);
    console.log(`  - リダイレクト先: /login`);
    console.log(`  - 保存する元のパス: ${location.pathname}`);

    // イベント作成ページの場合、リダイレクトループを回避するための特別な処理
    if (location.pathname === '/event/create') {
      console.log('イベント作成ページへのアクセスは認証が必要です');
      // 単純に状態と元のパスを保存してリダイレクト
      return <Navigate to="/login" state={{ from: '/event/create' }} replace />
    }
    
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }

  console.log(`🔐 ProtectedRoute - 認証済。表示許可: ${location.pathname}`)
  
  // イベント作成ページの場合の特別な処理
  if (location.pathname === '/event/create') {
    console.log('イベント作成ページの表示を確認');
  }
  
  return children
}
