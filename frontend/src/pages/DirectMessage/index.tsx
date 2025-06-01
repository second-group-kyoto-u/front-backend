import React, { useEffect, useState, useRef, ChangeEvent } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { uploadImage } from '@/api/upload';
import { useAuth } from '@/hooks/useAuth';
import { getDirectMessages, sendDirectMessage } from '@/api/friend';
import { getUserProfile } from '@/api/user';
// CSSファイル名がEventTalk.module.cssのままですが、内容に合わせて調整
import styles from './EventTalk.module.css'; // または './DirectMessage.module.css' に変更することをお勧めします

interface Message {
  id: string;
  content: string;
  sent_at: string;
  message_type: 'text' | 'image';
  sender_id: string; // メッセージの送信者ID
  image_url?: string; // image_url を追加
  sender?: { // メッセージに紐づくsenderの情報（もしAPIが返すなら）
    user_name: string;
    user_image_url: string | null;
  };
}

interface User {
  id: string;
  user_name: string;
  user_image_url: string | null;
}

const DirectMessagePage = () => {
  const { userId } = useParams<{ userId: string }>(); // userIdの型を明示
  const [messages, setMessages] = useState<Message[]>([]);
  const [partner, setPartner] = useState<User | null>(null);
  const [inputMessage, setInputMessage] = useState(''); // inputからinputMessageに変更
  const [sending, setSending] = useState(false); // 送信中の状態
  const [error, setError] = useState<string | null>(null); // エラーメッセージ
  const [loading, setLoading] = useState(true); // ロード中

  const messagesEndRef = useRef<HTMLDivElement>(null); // メッセージリストの最下部への参照
  const fileInputRef = useRef<HTMLInputElement>(null); // ファイル入力の参照

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedFilePreview, setSelectedFilePreview] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const navigate = useNavigate();
  const { user } = useAuth(); // useAuthフックからユーザー情報を取得
  const myId = user?.id; // ログイン中のユーザーID

  useEffect(() => {
    const fetchMessagesAndPartner = async () => {
      if (!userId) {
        setError('ユーザーIDが指定されていません。');
        setLoading(false);
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const [msgRes, userRes] = await Promise.all([
          getDirectMessages(userId),
          getUserProfile(userId)
        ]);
        setMessages(msgRes.messages);
        setPartner(userRes.user);
      } catch (err) {
        console.error('データ取得失敗:', err);
        setError('メッセージまたは相手ユーザーの情報の取得に失敗しました。');
      } finally {
        setLoading(false);
      }
    };
    fetchMessagesAndPartner();
  }, [userId]);

  // メッセージが更新されたら最下部にスクロール
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const isCurrentUser = (senderId: string | undefined): boolean => {
    // senderIdがundefinedの場合を考慮
    return senderId === myId;
  };

  const handleSend = async (messageType: 'text' | 'image', content: string | File) => {
    if (sending) return; // 送信中は多重送信を防ぐ

    setSending(true);
    setError(null);
    setUploadProgress(0); // アップロード進捗をリセット

    try {
      let messageContent: string;
      let actualMessageType: 'text' | 'image' = messageType;

      if (messageType === 'image' && content instanceof File) {
        const formData = new FormData();
        formData.append('image', content);

        const uploadRes = await uploadImage(formData, (progressEvent) => {
          if (progressEvent.total) {
            setUploadProgress(Math.round((progressEvent.loaded * 100) / progressEvent.total));
          }
        });
        messageContent = uploadRes.image_url; // アップロードされた画像のURL
      } else if (messageType === 'text' && typeof content === 'string') {
        if (!content.trim()) return; // 空白メッセージは送信しない
        messageContent = content.trim();
      } else {
        throw new Error('無効なメッセージタイプまたはコンテンツです。');
      }

      await sendDirectMessage(userId!, { content: messageContent, message_type: actualMessageType });

      // 送信後、最新のメッセージを再取得
      const updatedMessages = await getDirectMessages(userId!);
      setMessages(updatedMessages.messages);

      setInputMessage(''); // 入力フィールドをクリア
      setSelectedFile(null); // ファイル選択をクリア
      setSelectedFilePreview(null);
      setUploadProgress(0);

    } catch (err) {
      console.error('メッセージ送信失敗:', err);
      setError('メッセージの送信に失敗しました。');
    } finally {
      setSending(false);
    }
  };

  const handleTextareaKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // 改行を防ぐ
      handleSend('text', inputMessage); // Enterで送信
    }
  };

  const handleAttachClick = () => {
    fileInputRef.current?.click(); // ファイル選択ダイアログを開く
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setSelectedFilePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
      setInputMessage(''); // ファイル選択時はテキスト入力をクリア
    } else {
      setSelectedFile(null);
      setSelectedFilePreview(null);
    }
  };

  const cancelFileSelection = () => {
    setSelectedFile(null);
    setSelectedFilePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = ''; // input file の値をリセット
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedFile) {
      handleSend('image', selectedFile);
    } else {
      handleSend('text', inputMessage);
    }
  };

  const formatTimestamp = (timestamp: string | undefined): string => {
    if (!timestamp) return '';
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
      console.error('Invalid timestamp:', timestamp, e);
      return '';
    }
  };

  const getUserInitial = (userName: string | undefined): string => {
    return userName ? userName.charAt(0).toUpperCase() : '?';
  };

  // ユーザー名からランダムな色を生成する関数（簡易的な例）
  const getUserColor = (userName: string | undefined): string => {
    if (!userName) return '#ccc';
    const colors = ['#FFDDC1', '#D4EDDA', '#D1ECF1', '#CCE5FF', '#F8D7DA', '#FFF3CD'];
    let hash = 0;
    for (let i = 0; i < userName.length; i++) {
      hash = userName.charCodeAt(i) + ((hash << 5) - hash);
    }
    const colorIndex = Math.abs(hash % colors.length);
    return colors[colorIndex];
  };

  const renderImage = (imageUrl: string | undefined) => {
    if (!imageUrl) return null;
    return (
      <a href={imageUrl} target="_blank" rel="noopener noreferrer">
        <img src={imageUrl} alt="Uploaded" className={styles.uploadedImage} />
      </a>
    );
  };

  return (
    <div className={styles.pageContainer}>
      <div className={styles.header}>
        <button
          className={styles.backButton}
          onClick={() => navigate('/talks')} {/* トークリストページへ戻る */}
          aria-label="戻る"
        >
          ←
        </button>
        <h1 className={styles.title}>{partner?.user_name || 'DMルーム'}</h1>
        {/* DMにはメニューボタンは通常不要、もしプロフィール詳細へのリンクなら検討 */}
        {/* <button className={styles.menuButton} aria-label="メニュー" onClick={toggleMenu}>⋮</button> */}
      </div>

      <div className={styles.messageList}>
        {loading && <div className={styles.loadingMessage}>メッセージを読み込み中...</div>}
        {error && <div className={styles.errorMessage}>{error}</div>}

        {!loading && messages.length === 0 && (
          <div className={styles.noMessages}>
            メッセージはまだありません。最初のメッセージを送信しましょう！
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`${styles.messageItem} ${isCurrentUser(msg.sender_id) ? styles.sent : styles.received}`}
          >
            {/* アバター（自分のメッセージには表示しない） */}
            {!isCurrentUser(msg.sender_id) && (
              <div
                className={styles.avatar}
                style={{ backgroundColor: getUserColor(msg.sender?.user_name) }}
              >
                {msg.sender?.user_image_url ? (
                  <img
                    src={msg.sender.user_image_url}
                    alt={msg.sender.user_name}
                    className={styles.userAvatarImage}
                    onError={(e: React.SyntheticEvent<HTMLImageElement, Event>) => {
                      const target = e.currentTarget;
                      target.style.display = 'none';
                      if (target.parentElement) {
                         target.parentElement.textContent = getUserInitial(msg.sender?.user_name);
                         target.parentElement.style.display = 'flex';
                         target.parentElement.style.justifyContent = 'center';
                         target.parentElement.style.alignItems = 'center';
                      }
                    }}
                  />
                ) : (
                  getUserInitial(msg.sender?.user_name)
                )}
              </div>
            )}

            <div className={`${styles.messageContent} ${isCurrentUser(msg.sender_id) ? styles.sent : ''}`}>
              {/* 送信者名（自分のメッセージには表示しない） */}
              {!isCurrentUser(msg.sender_id) && (
                <div className={styles.senderName}>{msg.sender?.user_name || partner?.user_name || '不明なユーザー'}</div>
              )}

              {/* メッセージ内容 */}
              {msg.message_type === 'text' ? (
                <div className={styles.messageBubble}>{msg.content}</div>
              ) : (
                <div className={styles.imageMessage}>
                  {renderImage(msg.image_url)}
                </div>
              )}

              {/* タイムスタンプ */}
              <div className={styles.timestamp}>{formatTimestamp(msg.sent_at)}</div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* アップロード進捗表示 */}
      {uploadProgress > 0 && uploadProgress < 100 && (
        <div className={styles.uploadProgress}>
          <div
            className={styles.uploadProgressBar}
            style={{ width: `${uploadProgress}%` }}
          ></div>
          <span className={styles.uploadProgressText}>画像をアップロード中...</span>
        </div>
      )}

      {/* 選択ファイルの表示 */}
      {selectedFile && (
        <div className={styles.selectedFile}>
          {selectedFilePreview && (
            <img src={selectedFilePreview} alt="プレビュー" className={styles.imagePreview} />
          )}
          <span className={styles.selectedFileName}>{selectedFile.name}</span>
          <button
            onClick={cancelFileSelection}
            className={styles.cancelFileButton}
            aria-label="ファイル選択をキャンセル"
          >
            ×
          </button>
        </div>
      )}

      <form onSubmit={handleSubmit} className={styles.inputArea}>
        <button
          type="button"
          onClick={handleAttachClick}
          className={styles.attachButton}
          aria-label="ファイルを添付"
          disabled={sending}
        >
          📎
        </button>
        <input
          type="file"
          accept="image/*"
          ref={fileInputRef}
          onChange={handleFileChange}
          className={styles.fileInput}
          disabled={sending}
        />
        <textarea
          value={inputMessage} // newMessage から inputMessage に変更
          onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setInputMessage(e.target.value)}
          placeholder="メッセージを入力"
          className={styles.messageInput}
          disabled={!!selectedFile || sending}
          onKeyDown={handleTextareaKeyDown}
        />
        {/* アドバイザーモードのチェックボックスはDMでは不要なはずなので削除 */}
        {/* <div className={styles.adviserContainer}>...</div> */}
        <button
          type="submit"
          className={styles.sendButton}
          disabled={(!inputMessage.trim() && !selectedFile) || sending}
          aria-label="送信"
        >
          {sending ? '...' : '→'}
        </button>
      </form>

      {/* キャラクター選択モーダルやメニューはDMでは不要なはずなので削除 */}
      {/* {showCharacterModal && (...) } */}
      {/* {showMenu && (...) } */}
    </div>
  );
};

export default DirectMessagePage;