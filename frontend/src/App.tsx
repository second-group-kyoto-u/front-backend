// アプリのルート（ルーティングなど）
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Mypage from '@/pages/Mypage'
import LoginPage from '@/pages/Login'
import { useAuth } from '@/hooks/useAuth'

function App() {
  const { isAuthenticated } = useAuth()

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/mypage"
          element={
            isAuthenticated ? <Mypage /> : <Navigate to="/login" replace />
          }
        />
        {/* ルートパスに来たらマイページ or ログインに飛ばす */}
        <Route
          path="/"
          element={
            isAuthenticated ? <Navigate to="/mypage" /> : <Navigate to="/login" />
          }
        />
      </Routes>
    </Router>
  )
}

export default App
