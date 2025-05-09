import { ReactNode } from 'react'
import { useLocation } from 'react-router-dom'
import styles from './Layout.module.css'

interface Props {
  children: ReactNode
}

export default function Layout({ children }: Props) {
  const location = useLocation()

  return (
    <div className={styles.pageWrapper}>
      <div className={styles.content}>{children}</div>

      <div className={styles.fixedNav}>
        <a href="/events" className={styles.navItem}>👥<div>イベント</div></a>
        <a href="/threads" className={`${styles.navItem} ${location.pathname.startsWith('/threads') ? styles.active : ''}`}>📝<div>スレッド</div></a>
        <a href="/talk" className={styles.navItem}>💬<div>トーク</div></a>
        <a href="/mypage" className={`${styles.navItem} ${location.pathname === '/mypage' ? styles.active : ''}`}>👤<div>マイページ</div></a>
      </div>
    </div>
  )
}
