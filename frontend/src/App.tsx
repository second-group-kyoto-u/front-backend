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
import Layout from './components/Layout/Layout.tsx' // 固定メニューを全ページに共通化するためのレイアウト

function App(): JSX.Element {
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

        {/* 登録ページ */}
        <Route path="/register" element={<RegisterPage />} />

        {/* スレッド一覧（誰でも閲覧可能） */}
        <Route
          path="/threads"
          element={
            <Layout>
              <ThreadsPage />
            </Layout>
          }
        />

        {/* スレッド詳細 */}
        <Route
          path="/thread/:threadId"
          element={
            <Layout>
              <ThreadDetailPage />
            </Layout>
          }
        />

        {/* スレッド作成（要ログイン） */}
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

        {/* イベント一覧（誰でも閲覧可能） */}
        <Route
          path="/events"
          element={
            <Layout>
              <EventsPage />
            </Layout>
          }
        />

        {/* イベント詳細 */}
        <Route
          path="/event/:eventId"
          element={
            <Layout>
              <EventDetailPage />
            </Layout>
          }
        />

        {/* イベントトーク */}
        <Route
          path="/event/:eventId/talk"
          element={
            <Layout>
              <EventTalkPage />
            </Layout>
          }
        />

        {/* マイページ */}
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

        {/* プロフィール編集 */}
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

        {/* 初期表示：マイページへ */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Navigate to="/mypage" replace />
            </ProtectedRoute>
          }
        />

        {/* 404 */}
        <Route path="*" element={<div>404 - ページが見つかりません</div>} />
      </Routes>
    </Router>
  )
}

export default App
