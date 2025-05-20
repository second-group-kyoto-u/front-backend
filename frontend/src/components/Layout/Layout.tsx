import React, { useEffect } from 'react'
import { useLocation, Link } from 'react-router-dom'
import styles from './Layout.module.css'

interface Props {
  children: React.ReactNode
}

export default function Layout({ children }: Props) {
  const location = useLocation()

  // パスの変更をログに出力（デバッグ用）
  useEffect(() => {
    console.log('現在のパス:', location.pathname);
  }, [location.pathname]);

  // 現在のパスが特定のパターンに一致するか確認する関数
  const isPathMatch = (pattern: string) => {
    if (pattern === '/events') {
      return location.pathname === '/events';
    } else if (pattern === '/threads') {
      return location.pathname.startsWith('/threads');
    } else if (pattern === '/talk') {
      return location.pathname.startsWith('/talk');
    } else if (pattern === '/mypage') {
      return location.pathname === '/mypage';
    }
    return false;
  };

  // イベント作成ページかどうかをチェック
  const isEventCreatePage = location.pathname === '/event/create';

  return (
    <div className={styles.pageWrapper}>
      <div className={styles.content}>
        {isEventCreatePage && <div className={styles.debugInfo}>イベント作成ページ</div>}
        {children}
      </div>

      <div className={styles.fixedNav}>
        <Link to="/events" className={`${styles.navItem} ${isPathMatch('/events') ? styles.active : ''}`}>
          <span className="material-icons">event</span>
          <div>イベント</div>
        </Link>

        <Link to="/threads" className={`${styles.navItem} ${isPathMatch('/threads') ? styles.active : ''}`}>
          <span className="material-icons">forum</span>
          <div>スレッド</div>
        </Link>

        <Link to="/talk" className={styles.navItem}>
          <span className="material-icons">chat</span>
          <div>トーク</div>
        </Link>

        <Link to="/mypage" className={`${styles.navItem} ${isPathMatch('/mypage') ? styles.active : ''}`}>
          <span className="material-icons">person</span>
          <div>マイページ</div>
        </Link>
      </div>

    </div>
  )
}
