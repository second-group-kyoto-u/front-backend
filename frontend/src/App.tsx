import React, { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom'
import LoginPage from './pages/Login'
import Mypage from './pages/Mypage'
import EditMypage from './pages/EditMypage'
import UserProfilePage from './pages/UserProfile'
import ThreadsPage from './pages/Threads'
import ThreadDetailPage from './pages/ThreadDetail'
import CreateThreadPage from './pages/CreateThread'
import EventsPage from './pages/Events'
import CreateEventPage from './pages/CreateEvent'
import EventDetailPage from './pages/EventDetail'
import EventTalkPage from './pages/EventTalk'
import RegisterPage from './pages/Register'
import TalkListPage from './pages/TalkList'
import DirectMessagePage from './pages/DirectMesage'
import './App.css'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AuthRoute } from './components/AuthRoute'
import Layout from './components/Layout/Layout.tsx' // 固定メニューを全ページに共通化するためのレイアウト

// ルーティングのデバッグ用コンポーネント
const RouteLogger = () => {
  const location = useLocation();
  
  useEffect(() => {
    console.log('ルーティング: 現在のパス:', location.pathname);
    console.log('ルーティング: 完全なURL:', window.location.href);
  }, [location]);
  
  return null;
};

function App(): JSX.Element {
  return (
    <Router>
      <RouteLogger />
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

        {/* イベント作成（認証確認なし） */}
        <Route
          path="/event/create"
          element={
            <Layout>
              {console.log('イベント作成ページをレンダリングします')}
              <CreateEventPage />
            </Layout>
          }
        />

        {/* 重要: イベントIDのパターンよりも先にマッチさせる */}
        <Route
          path="/event/create/*"
          element={
            <Layout>
              {console.log('イベント作成ページ（ワイルドカードあり）をレンダリングします')}
              <CreateEventPage />
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

        {/* 参加中のイベントトークとDMの表示 */}
        <Route 
          path="/talk" 
          element={
            <Layout>
              <TalkListPage />
            </Layout>
          }
        />

        {/* DM */}
        <Route 
          path="/friend/:userId/dm"
          element={
            <Layout>
              <DirectMessagePage />
            </Layout>
          }
        />



        {/* ユーザープロフィール */}
        <Route
          path="/user/:userId"
          element={
            <Layout>
              <UserProfilePage />
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

        {/* 初期表示：イベントページへ */}
        <Route
          path="/"
          element={<Navigate to="/events" replace />}
        />

        {/* 404 */}
        <Route 
          path="*" 
          element={
            <div>
              <h1>404 - ページが見つかりません</h1>
              <p>URL: {window.location.href}</p>
            </div>
          } 
        />
      </Routes>
    </Router>
  )
}

export default App
