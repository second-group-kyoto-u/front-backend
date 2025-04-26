import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/Login'
import Mypage from './pages/Mypage'
import ThreadsPage from './pages/Threads'
import ThreadDetailPage from './pages/ThreadDetail'
import CreateThreadPage from './pages/CreateThread'
import EventsPage from './pages/Events'
import RegisterPage from './pages/Register'
import './App.css'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AuthRoute } from './components/AuthRoute'

function App(): JSX.Element {
  console.log('🔧 App - ルーティングレンダリング中')

  return (
    <Router>
      <Routes>
        {/* ログインページ（未ログインユーザー向け） */}
        <Route 
          path="/login" 
          element={
            <AuthRoute>
              <LoginPage />
            </AuthRoute>
          } 
        />

        {/* マイページ（ログイン済みのみ） */}
        <Route
          path="/mypage"
          element={
            <ProtectedRoute>
              <Mypage />
            </ProtectedRoute>
          }
        />

        {/* スレッドページ（誰でも閲覧可能） */}
        <Route path="/threads" element={<ThreadsPage />} />
        <Route path="/threads/:id" element={<ThreadDetailPage />} />

        {/* スレッド作成（ログイン必須） */}
        <Route
          path="/threads/create"
          element={
            <ProtectedRoute>
              <CreateThreadPage />
            </ProtectedRoute>
          }
        />

        {/* イベント（誰でも閲覧可能） */}
        <Route path="/events" element={<EventsPage />} />

        {/* 登録ページ */}
        <Route path="/register" element={<RegisterPage />} />

        {/* 初期表示はマイページへ（ログインが必要） */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Navigate to="/mypage" replace />
            </ProtectedRoute>
          }
        />

        {/* 404ルート（存在しないパス） */}
        <Route path="*" element={<div>404 - ページが見つかりません</div>} />
      </Routes>
    </Router>
  )
}

export default App
