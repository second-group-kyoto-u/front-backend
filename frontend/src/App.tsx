import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/Login'
import Mypage from './pages/Mypage'
import EditMypage from './pages/EditMypage'
import ThreadsPage from './pages/Threads'
import ThreadDetailPage from './pages/ThreadDetail'
import CreateThreadPage from './pages/CreateThread'
import EventsPage from './pages/Events'
import EventDetailPage from './pages/EventDetail'
import EventTalkPage from './pages/EventTalk'
import RegisterPage from './pages/Register'
import './App.css'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AuthRoute } from './components/AuthRoute'
import Layout from './components/Layout'

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
              <Layout>
                <Mypage />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* プロフィール編集ページ */}
        <Route 
          path="/edit-mypage" 
          element={
            <ProtectedRoute>
              <Layout>
                <EditMypage />
              </Layout>
            </ProtectedRoute>
          } 
        />

        {/* スレッドページ（誰でも閲覧可能） */}
        <Route path="/threads" element={<Layout><ThreadsPage /></Layout>} />
        <Route path="/thread/:threadId" element={<Layout><ThreadDetailPage /></Layout>} />

        {/* スレッド作成（ログイン必須） */}
        <Route
          path="/threads/create"
          element={
            <ProtectedRoute>
              <Layout>
                <CreateThreadPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* イベント（誰でも閲覧可能） */}
        <Route path="/events" element={<Layout><EventsPage /></Layout>} />
        <Route path="/event/:eventId" element={<Layout><EventDetailPage /></Layout>} />

        {/* イベント参加者用トークルーム */}
        <Route path="/event/:eventId/talk" element={<Layout><EventTalkPage /></Layout>} />

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