import { useEffect, useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import styles from './VerificationSuccess.module.css'

function VerificationSuccessPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [status, setStatus] = useState('approved') // approved, rejected, extraction_failed
  const [age, setAge] = useState<number | null>(null)
  
  useEffect(() => {
    // 前のページから渡されたstate情報を取得
    if (location.state) {
      const { status: resultStatus, age: resultAge } = location.state as any
      setStatus(resultStatus || 'approved')
      setAge(resultAge || null)
    }
    
    // 成功の場合のみ自動遷移
    if (status === 'approved') {
      const timer = setTimeout(() => {
        navigate('/mypage')
      }, 5000)
      
      return () => clearTimeout(timer)
    }
  }, [navigate, status])
  
  const getStatusInfo = () => {
    switch (status) {
      case 'approved':
        return {
          icon: '✓',
          title: '年齢認証が完了しました！',
          iconClass: styles.successIcon,
          messages: [
            '年齢認証書類の確認が完了しました。',
            age ? `推定年齢: ${age}歳` : '',
            'すべての機能をご利用いただけます。'
          ].filter(Boolean)
        }
      case 'rejected':
        return {
          icon: '✗',
          title: '年齢認証に失敗しました',
          iconClass: styles.errorIcon,
          messages: [
            '申し訳ございませんが、年齢認証を通過できませんでした。',
            age ? `推定年齢: ${age}歳` : '',
            '18歳以上の方のみご利用いただけます。'
          ].filter(Boolean)
        }
      case 'extraction_failed':
      default:
        return {
          icon: '⚠',
          title: '書類の読み取りに失敗しました',
          iconClass: styles.warningIcon,
          messages: [
            '書類から年齢情報を読み取れませんでした。',
            '以下の点をご確認の上、再度お試しください：',
            '• 書類全体が鮮明に写っている',
            '• 光の反射で文字が見えない部分がない',
            '• 生年月日が明確に記載されている'
          ]
        }
    }
  }
  
  const statusInfo = getStatusInfo()
  
  return (
    <div className={styles.pageBackground}>
      <div className={styles.container}>
        <div className={statusInfo.iconClass}>{statusInfo.icon}</div>
        <h2 className={styles.title}>{statusInfo.title}</h2>
        
        <div className={styles.message}>
          {statusInfo.messages.map((message, index) => (
            <p key={index}>{message}</p>
          ))}
        </div>
        
        <div className={styles.buttonGroup}>
          {status === 'approved' ? (
            <>
              <Link to="/mypage" className={styles.primaryButton}>
                マイページに戻る
              </Link>
              <Link to="/events" className={styles.secondaryButton}>
                イベント一覧を見る
              </Link>
            </>
          ) : (
            <>
              <Link to="/age-verification" className={styles.primaryButton}>
                再度年齢認証を行う
              </Link>
              <Link to="/mypage" className={styles.secondaryButton}>
                マイページに戻る
              </Link>
            </>
          )}
        </div>
        
        {status === 'approved' && (
          <p className={styles.autoRedirect}>
            5秒後に自動的にマイページに移動します...
          </p>
        )}
      </div>
    </div>
  )
}

export default VerificationSuccessPage 