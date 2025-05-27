import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { createEvent } from '@/api/event';
import { uploadEventImage } from '@/api/upload';
import { getAreas, Area } from '@/api/area';
import styles from './CreateEvent.module.css';

// APIでタグを取得するべきだが、簡略化のためここで定義
const AVAILABLE_TAGS = [
  '自然', 'グルメ', 'アウトドア', 'スポーツ', '文化', 'ショッピング', '観光', '歴史'
];



const CreateEventPage: React.FC = () => {
  const navigate = useNavigate();
  
  const [areas, setAreas] = useState<Area[]>([]);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    area_id: '',
    limit_persons: 10,
    tags: [] as string[],
    eventDate: '',
    startTime: '',
    endTime: '',
    location: '',
    image_id: '',
  });
  
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  

  useEffect(() => {
    (async () => {
      try {
        const fetchedAreas = await getAreas();
        setAreas(fetchedAreas);
        console.log("送信されるarea_id", formData.area_id);
      } catch (err) {
        console.error('エリアの取得に失敗しました', err);
      }
    })();
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const handleTagToggle = (tag: string) => {
    setFormData(prev => {
      const tags = [...prev.tags];
      if (tags.includes(tag)) {
        return { ...prev, tags: tags.filter(t => t !== tag) };
      } else {
        return { ...prev, tags: [...tags, tag] };
      }
    });
  };
  
  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setImage(file);
      
      // プレビュー用のURL生成
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // バリデーション
    if (!formData.title.trim()) {
      setError('イベントのタイトルを入力してください');
      return;
    }
    if (!formData.description.trim()) {
      setError('イベントの説明を入力してください');
      return;
    }
    if (!formData.area_id) {
      setError('開催地域を選択してください');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      // 画像のアップロード処理
      let imageId = '';
      if (image) {
        try {
          setUploadProgress(10);
          const uploadResult = await uploadEventImage(image);
          imageId = uploadResult.image_id;
          setUploadProgress(100);
        } catch (uploadErr) {
          console.error('画像アップロードエラー:', uploadErr);
          setError('画像のアップロードに失敗しました。');
          setLoading(false);
          return;
        }
      }
      
      // イベント作成APIを呼び出す
      const eventData = {
        title: formData.title,
        description: formData.description,
        area_id: formData.area_id,
        limit_persons: formData.limit_persons,
        tags: formData.tags,
        event_location: formData.location,
        image_id: imageId || undefined,
        // 日付と時間があれば追加
        ...(formData.eventDate && {
          event_date: formData.eventDate
        }),
        ...(formData.startTime && {
          start_time: formData.startTime
        }),
        ...(formData.endTime && {
          end_time: formData.endTime
        })
      };
      
      const result = await createEvent(eventData);
      
      // 成功したら詳細ページへ遷移
      navigate(`/event/${result.event.id}`);
    } catch (err) {
      console.error('イベント作成エラー:', err);
      setError('イベントの作成に失敗しました。もう一度お試しください。');
    } finally {
      setLoading(false);
      setUploadProgress(0);
    }
  };
  
  const handleCancel = () => {
    navigate('/events'); // 数値ではなく文字列のパスを指定する
  };
  
  return (
    <div className={styles.pageBackground}>
      <div className={styles.createEventContainer}>
        <div className={styles.createEventHeader}>
          <button onClick={handleCancel} className={styles.backButton}>
            ← 戻る
          </button>
          <h1 className={styles.pageTitle}>イベント作成</h1>
        </div>
        
        {error && <div className={styles.errorContainer}>{error}</div>}
        
        <form onSubmit={handleSubmit} className={styles.createEventForm}>
          {/* イベント画像 */}
          <div className={styles.imageUploadContainer}>
            <label htmlFor="event-image" className={styles.imageUploadLabel}>
              {imagePreview ? (
                <img 
                  src={imagePreview} 
                  alt="イベント画像プレビュー" 
                  className={styles.imagePreview} 
                />
              ) : (
                <div className={styles.uploadPlaceholder}>
                  <span>+</span>
                  <span>画像をアップロード</span>
                </div>
              )}
              {uploadProgress > 0 && uploadProgress < 100 && (
                <div className={styles.uploadProgressContainer}>
                  <div 
                    className={styles.uploadProgressBar} 
                    style={{ width: `${uploadProgress}%` }} 
                  />
                </div>
              )}
            </label>
            <input
              type="file"
              id="event-image"
              accept="image/*"
              onChange={handleImageChange}
              className={styles.imageInput}
            />
          </div>
          
          {/* イベントタイトル */}
          <div className={styles.formGroup}>
            <label htmlFor="title" className={styles.formLabel}>イベント名:</label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleInputChange}
              className={styles.formInput}
              placeholder="イベントのタイトル"
              required
            />
          </div>
          
          {/* イベント説明 */}
          <div className={styles.formGroup}>
            <label htmlFor="description" className={styles.formLabel}>イベントの説明:</label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              className={styles.formTextarea}
              placeholder="イベントの詳細説明"
              rows={5}
              required
            />
          </div>
          
          {/* タグ選択 */}
          <div className={styles.formGroup}>
            <label className={styles.formLabel}>タグ:</label>
            <div className={styles.tagContainer}>
              {AVAILABLE_TAGS.map(tag => (
                <button
                  type="button"
                  key={tag}
                  className={`${styles.tagButton} ${formData.tags.includes(tag) ? styles.tagSelected : ''}`}
                  onClick={() => handleTagToggle(tag)}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>
          
          {/* 開催日時 */}
          <div className={styles.formGroup}>
            <label htmlFor="eventDate" className={styles.formLabel}>開催日時:</label>
            <input
              type="date"
              id="eventDate"
              name="eventDate"
              value={formData.eventDate}
              onChange={handleInputChange}
              className={styles.formInput}
              required
            />
          </div>
          
          {/* 開催時間 */}
          <div className={styles.formTimeGroup}>
            <div>
              <label htmlFor="startTime" className={styles.formLabel}>開始時間:</label>
              <input
                type="time"
                id="startTime"
                name="startTime"
                value={formData.startTime}
                onChange={handleInputChange}
                className={styles.formInput}
                required
              />
            </div>
            <div>
              <label htmlFor="endTime" className={styles.formLabel}>終了時間:</label>
              <input
                type="time"
                id="endTime"
                name="endTime"
                value={formData.endTime}
                onChange={handleInputChange}
                className={styles.formInput}
              />
            </div>
          </div>
          
          {/* 開催場所 */}
          <div className={styles.formGroup}>
            <label htmlFor="location" className={styles.formLabel}>開催場所:</label>
            <input
              type="text"
              id="location"
              name="location"
              value={formData.location}
              onChange={handleInputChange}
              className={styles.formInput}
              placeholder="開催場所の詳細"
              required
            />
          </div>
          
          {/* エリア選択 */}
          <div className={styles.formGroup}>
            <label htmlFor="area_id" className={styles.formLabel}>開催地域:</label>
            <select
              id="area_id"
              name="area_id"
              value={formData.area_id}
              onChange={handleInputChange}
              className={styles.formSelect}
              required
            >
              <option value="">選択してください</option>
              {areas.map(area => (
                <option key={area.id} value={area.id}>
                  {area.name}
                </option>
              ))}
            </select>
          </div>
          
          {/* 参加人数制限 */}
          <div className={styles.formGroup}>
            <label htmlFor="limit_persons" className={styles.formLabel}>定員:</label>
            <input
              type="number"
              id="limit_persons"
              name="limit_persons"
              value={formData.limit_persons}
              onChange={handleInputChange}
              className={styles.formInput}
              min={1}
              max={100}
              required
            />
          </div>
          
          {/* 送信ボタン */}
          <div className={styles.formActions}>
            <button
              type="submit"
              className={styles.submitButton}
              disabled={loading}
            >
              {loading ? '作成中...' : 'イベントを作成'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateEventPage; 