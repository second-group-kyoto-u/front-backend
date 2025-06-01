// src/pages/SearchFilterPage.tsx
import { useNavigate } from 'react-router-dom'
import { useState } from 'react'
import styles from './Search.module.css'

function SearchFilterPage() {
  const navigate = useNavigate()

  const [keyword, setKeyword] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [location, setLocation] = useState('')
  const [minCapacity, setMinCapacity] = useState('')
  const [maxCapacity, setMaxCapacity] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const params = new URLSearchParams()

    if (keyword) params.append('keyword', keyword)
    if (startDate) params.append('startDate', startDate)
    if (endDate) params.append('endDate', endDate)
    if (location) params.append('location', location)
    if (minCapacity) params.append('minCapacity', minCapacity)
    if (maxCapacity) params.append('maxCapacity', maxCapacity)

    navigate(`/events?${params.toString()}`)
  }

  return (
    <div className={styles.searchPage}>
      <div className={styles.searchTitle}>← イベント検索</div>

      <form className={styles.searchForm} onSubmit={handleSubmit}>
        {/* キーワード */}
        <div className={styles.inputGroup}>
          <input
            type="text"
            placeholder="キーワード"
            value={keyword}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setKeyword(e.target.value)}
          />
        </div>

        {/* 開催日時 */}
        <div className={styles.inputGroup}>
          <label>開催日時</label>
          <div className={styles.inputRow}>
            <input
              type="date"
              value={startDate}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setStartDate(e.target.value)}
              placeholder="YYYY/MM/DD"
            />
            <input
              type="date"
              value={endDate}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEndDate(e.target.value)}
              placeholder="YYYY/MM/DD"
            />
          </div>
        </div>

        {/* 開催場所 */}
        <div className={styles.inputGroup}>
          <label>開催場所</label>
          <input
            type="text"
            placeholder="開催地域"
            value={location}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setLocation(e.target.value)}
          />
        </div>

        {/* 定員 */}
        <div className={styles.inputGroup}>
          <label>定員</label>
          <div className={styles.inputRow}>
            <select
              value={minCapacity}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setMinCapacity(e.target.value)}
            >
              <option value="">最小人数</option>
              {[...Array(10)].map((_, i) => (
                <option key={i + 1} value={i + 1}>{i + 1}人〜</option>
              ))}
            </select>

            <select
              value={maxCapacity}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setMaxCapacity(e.target.value)}
            >
              <option value="">最大人数</option>
              {[...Array(10)].map((_, i) => (
                <option key={i + 1} value={i + 1}>{i + 1}人以下</option>
              ))}
            </select>
          </div>
        </div>

        <button className={styles.searchButton}>イベントを検索</button>
      </form>
    </div>
  )
}

export default SearchFilterPage