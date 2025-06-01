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
import DirectMessagePage from './pages/DirectMessage/index.tsx'
import AgeVerificationPage from './pages/AgeVerification/index.tsx'
import VerificationSuccessPage from './pages/VerificationSuccess/index.tsx'
import './App.css'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AuthRoute } from './components/AuthRoute'
import Layout from './components/Layout/Layout.tsx' // 固定メニューを全ページに共通化するためのレイアウト
import CreateNewDMPage from './pages/CreateNewDM/index.tsx'

// ルーティングのデバッグ用コンポーネント
const RouteLogger = () => {
  const location = useLocation();
  
  useEffect(() => {
    console.log('ルーティング: 現在のパス:', location.pathname);
    console.log('ルーティング: 完全なURL:', window.location.href);
  }, [location]);
  
  return null;
};

function App() {
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

        {/* イベント作成（認証が必要） */}
        <Route
          path="/event/create"
          element={
            <ProtectedRoute>
              <Layout>
                {console.log('イベント作成ページをレンダリングします')}
                <CreateEventPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* 重要: イベントIDのパターンよりも先にマッチさせる */}
        <Route
          path="/event/create/*"
          element={
            <ProtectedRoute>
              <Layout>
                {console.log('イベント作成ページ（ワイルドカードあり）をレンダリングします')}
                <CreateEventPage />
              </Layout>
            </ProtectedRoute>
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

        {/* イベントキャラクター選択 - EventTalkで実装しているのでリダイレクト */}
        <Route
          path="/event/:eventId/character-select"
          element={
            <Navigate to="../talk" replace />
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

        {/* DM（簡潔なパス） */}
        <Route 
          path="/dm/:userId"
          element={
            <Layout>
              <DirectMessagePage />
            </Layout>
          }
        />

        {/* 新規DMの作成（簡潔なパス） */}
        <Route 
          path="/dm/new"
          element={
            <Layout>
              <CreateNewDMPage />
            </Layout>
          }
        />

        {/* 互換性のため古いパスもサポート */}
        <Route 
          path="/friend/:userId/dm"
          element={<Navigate to={`/dm/${window.location.pathname.split('/')[2]}`} replace />}
        />

        <Route 
          path="/friend/create-DMpage"
          element={<Navigate to="/dm/new" replace />}
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

        {/* 年齢認証 */}
        <Route
          path="/age-verification"
          element={
            <ProtectedRoute>
              <Layout>
                <AgeVerificationPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* 年齢認証成功 */}
        <Route
          path="/verification-success"
          element={
            <ProtectedRoute>
              <Layout>
                <VerificationSuccessPage />
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
            <Layout>
              <div style={{ padding: '2rem', textAlign: 'center' }}>
                <h1>404 - ページが見つかりません</h1>
                <p>お探しのページは存在しないか、移動された可能性があります。</p>
                <div style={{ marginTop: '1rem' }}>
                  <button 
                    onClick={() => window.location.href = '/events'}
                    style={{ 
                      margin: '0.5rem',
                      padding: '0.5rem 1rem',
                      backgroundColor: '#5c4033',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    イベント一覧に戻る
                  </button>
                  <button 
                    onClick={() => window.location.href = '/login'}
                    style={{ 
                      margin: '0.5rem',
                      padding: '0.5rem 1rem',
                      backgroundColor: '#888',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    ログイン
                  </button>
                </div>
                <small style={{ display: 'block', marginTop: '1rem', color: '#888' }}>
                  URL: {window.location.href}
                </small>
              </div>
            </Layout>
          } 
        />
      </Routes>
    </Router>
  )
}

export default App
