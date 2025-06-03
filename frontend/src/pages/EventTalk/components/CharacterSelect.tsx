import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import styles from './CharacterSelect.module.css';
import { getCharacters, startEvent } from '@/api/event';

// キャラクターの型定義
type Character = {
  id: string;
  name: string;
  description: string;
  personality: string;
  speech_pattern: string;
  interests: string;
  traits: string;
  favorite_trip?: string;
  avatar_url?: string;
};

// onSelectとisModalをpropsとして受け取る
interface Props {
  onSelect?: () => void;
  isModal?: boolean;
}

const CharacterSelect: React.FC<Props> = ({ onSelect, isModal = false }) => {
  const { eventId } = useParams();
  const navigate = useNavigate();
  const [selectedCharacter, setSelectedCharacter] = useState<string | null>(null);
  const [expandedCharacter, setExpandedCharacter] = useState<string | null>(null);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // APIからキャラクター情報を取得
  useEffect(() => {
    const fetchCharacters = async () => {
      try {
        setLoading(true);
        const response = await getCharacters();
        if (response && response.characters) {
          setCharacters(response.characters);
        } else {
          // APIデータがない場合はデフォルトデータを使用
          setCharacters(defaultCharacters);
        }
      } catch (err) {
        console.error('キャラクター取得エラー:', err);
        setError('キャラクター情報の取得に失敗しました。デフォルトデータを表示します。');
        // エラー時はデフォルトデータを使用
        setCharacters(defaultCharacters);
      } finally {
        setLoading(false);
      }
    };

    fetchCharacters();
  }, []);

  // デフォルトのキャラクターデータ（APIから取得できない場合のフォールバック）
  const defaultCharacters: Character[] = [
    {
      id: 'nyanta',
      name: 'ニャンタ',
      description: 'おしゃべり好きな猫キャラクター',
      personality: '気まぐれで少しツンデレ。だけど話が盛り上がるとノリがいい。',
      speech_pattern: 'ふーん、それ、ちょっと面白そうじゃない？」「ま、気が向いたら話してあげるニャ',
      interests: 'グルメ、隠れ家的カフェ、フォトスポット',
      traits: '突然「そういえばさ…」と話題を切り出してくれるけど、興味がないとスルーすることもある。だけど当たるとツボ。'
    },
    {
      id: 'hitsuji',
      name: 'ひつじのひつじ',
      description: '優しく穏やかな羊キャラクター',
      personality: '温厚で優しく、いつも相手の話をじっくり聞いてくれる。少し控えめだが頼りになる。',
      speech_pattern: 'そうなんですね～。もっと教えてください」「一緒に考えてみましょうか～',
      interests: '自然、ハンドクラフト、ハーブティー、瞑想',
      traits: '相手の話をしっかり受け止め、共感してくれる。時々ぼーっとすることもあるが、アドバイスは的確。'
    },
    {
      id: 'koko',
      name: 'ココ',
      description: 'おしゃべりで社交的なラッコキャラクター',
      personality: 'おしゃべりで社交的、みんなのムードメーカー。ちょっと子どもっぽいけど和ませ上手。',
      speech_pattern: 'ねぇねぇ、それ聞いたことある〜！」「あっ、それ面白そうだね！もっと話して〜！',
      interests: 'ゲーム、恋バナ、ちょっとした心理テストや性格診断',
      traits: 'すぐに距離を縮めてくれるタイプで、初対面の人が多い旅先で特に活躍。笑いを生む話題が得意。'
    },
    {
      id: 'fukurou',
      name: 'フクロウくん',
      description: '博識で真面目なフクロウキャラクター',
      personality: '知的で物事を深く考える。情報通で、「伝えなきゃ」という使命感がある。',
      speech_pattern: 'これは重要なポイントです」「実はこんな情報もあるんですよ。知っておいた方がいいでしょう',
      interests: '読書、歴史、ミステリー、データ分析',
      traits: '物事の裏側にある情報を探るのが得意。時に話が長くなることもあるが、その情報は貴重なものが多い。'
    },
    {
      id: 'toraberu',
      name: 'トラベル',
      description: '冒険好きな虎キャラクター',
      personality: '活発でエネルギッシュ。常に新しいことに挑戦したがる冒険家タイプ。',
      speech_pattern: 'よーし、行くぞ！」「それ、超楽しそうじゃん！やってみよう！',
      interests: '旅行、アウトドア、スポーツ、新しい食べ物',
      traits: '行動力があり、どんな提案にも「やってみよう！」と前向き。時に無謀だが、その熱意は周りを巻き込む。'
    }
  ];

  const handleCharacterSelect = (characterId: string) => {
    setSelectedCharacter(characterId);
  };

  const handleToggleDetails = (characterId: string) => {
    if (expandedCharacter === characterId) {
      setExpandedCharacter(null);
    } else {
      setExpandedCharacter(characterId);
    }
  };

  const handleStartEvent = async () => {
    if (!selectedCharacter) {
      alert('キャラクターを選択してください');
      return;
    }
    
    console.log('キャラクター選択完了:', selectedCharacter);
    // 確実にsessionStorageに保存
    sessionStorage.setItem('selectedCharacter', selectedCharacter);
    
    try {
      console.log('イベント開始APIを呼び出します:', eventId);
      const response = await startEvent(eventId as string);
      console.log('イベント開始API成功:', response);
      
      // onSelectがあれば呼び出す（モーダルを閉じる）
      if (onSelect) {
        console.log('親コンポーネントのonSelectを呼び出します');
        onSelect();
      } else {
        console.log('イベントトークページに遷移します');
        navigate(`/event/${eventId}/talk`);
      }
    } catch (error) {
      console.error('イベント開始エラー:', error);
      alert('イベントの開始に失敗しました。もう一度お試しください。');
    }
  };

  // 画像URLを処理する関数
  const processImageUrl = (url: string | null): string => {
    if (!url) return '/default-avatar.jpg';
    
    // MinIOのURLを修正
    if (url.includes('localhost:9000') || url.includes('127.0.0.1:9000') || url.includes('minio:9000')) {
      // URLがローカルのMinioを指している場合、nginxプロキシ経由のパスに修正
      const pathMatch = url.match(/\/([^\/]+)\/(.+)$/);
      if (pathMatch) {
        const bucket = pathMatch[1];
        const key = pathMatch[2];
        // nginxプロキシ経由でアクセス（/minio/パス）
        const baseUrl = window.location.origin;
        return `${baseUrl}/minio/${bucket}/${key}`;
      }
    }
    
    // 既にプロキシ経由のパスを使用している場合はそのまま返す
    if (url.includes('/minio/')) {
      return url;
    }
    
    return url;
  };

  if (loading) {
    return <div className={styles.container}>キャラクター情報を読み込み中...</div>;
  }

  // モーダル用の簡略化されたUIを表示
  if (isModal) {
    return (
      <div className={styles.modalContainer}>
        <h2 className={styles.modalTitle}>botのキャラクターを選択しよう！</h2>
        
        {error && <div className={styles.error}>{error}</div>}
        
        <div className={styles.compactCharacterList}>
          {characters.map((character) => (
            <div key={character.id} className={styles.compactCharacterWrapper}>
              <div 
                className={`${styles.compactCharacterItem} ${selectedCharacter === character.id ? styles.compactCharacterItemSelected : ''}`}
                onClick={() => handleCharacterSelect(character.id)}
              >
                <div className={styles.compactCharacterAvatar}>
                  {character.avatar_url ? (
                    <img 
                      src={processImageUrl(character.avatar_url)} 
                      alt={character.name} 
                      className={styles.compactAvatarImage}
                      onError={(e: React.ChangeEvent<HTMLImageElement>) => {
                        const target = e.target;
                        target.style.display = 'none';
                        target.parentElement?.classList.add(styles.avatarPlaceholder);
                      }}
                    />
                  ) : (
                    <div className={styles.avatarPlaceholder}></div>
                  )}
                </div>
                <div className={styles.compactCharacterInfo}>
                  <div className={styles.compactCharacterName}>{character.name}</div>
                  <div className={styles.compactCharacterDesc}>{character.description}</div>
                </div>
                <div className={styles.compactControls}>
                  <input
                    type="radio"
                    name="character"
                    checked={selectedCharacter === character.id}
                    onChange={() => {}}
                    className={styles.compactRadioInput}
                  />
                  <button 
                    className={styles.compactToggleButton}
                    onClick={(e: any) => {
                      e.stopPropagation();
                      handleToggleDetails(character.id);
                    }}
                  >
                    {expandedCharacter === character.id ? '▲' : '▼'}
                  </button>
                </div>
              </div>
              
              <div className={`${styles.compactCharacterDetails} ${expandedCharacter === character.id ? styles.expanded : styles.collapsed}`}>
                <div className={styles.detailSection}>
                  <h3>性格</h3>
                  <p>{character.personality}</p>
                </div>
                
                <div className={styles.detailSection}>
                  <h3>口調</h3>
                  <p>{character.speech_pattern}</p>
                </div>
                
                <div className={styles.detailSection}>
                  <h3>得意な話題</h3>
                  <p>{character.interests}</p>
                </div>
                
                <div className={styles.detailSection}>
                  <h3>特徴</h3>
                  <p>{character.traits}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        <button 
          className={styles.modalStartButton}
          onClick={handleStartEvent}
          disabled={!selectedCharacter}
        >
          選択してイベントを開始する
        </button>
      </div>
    );
  }

  // 通常の完全なUIを表示
  return (
    <div className={styles.container}>
      <h1 className={styles.title}>botのキャラクターを選択しよう！</h1>
      
      {error && <div className={styles.error}>{error}</div>}
      
      <div className={styles.characterList}>
        {characters.map((character) => (
          <div 
            key={character.id} 
            className={`${styles.characterItem} ${selectedCharacter === character.id ? styles.characterItemSelected : ''}`}
          >
            <div className={styles.characterHeader}>
              <label className={styles.radioContainer}>
                <input
                  type="radio"
                  name="character"
                  checked={selectedCharacter === character.id}
                  onChange={() => handleCharacterSelect(character.id)}
                  className={styles.radioInput}
                />
                <span className={styles.radioCheckmark}></span>
              </label>
              
              <div className={styles.characterAvatar}>
                {character.avatar_url ? (
                  <img 
                    src={processImageUrl(character.avatar_url)} 
                    alt={character.name} 
                    className={styles.avatarImage}
                    onError={(e: React.ChangeEvent<HTMLImageElement>) => {
                      const target = e.target;
                      target.style.display = 'none';
                      target.parentElement?.classList.add(styles.avatarPlaceholder);
                    }}
                  />
                ) : (
                  <div className={styles.avatarPlaceholder}></div>
                )}
              </div>
              
              <div className={styles.characterName}>{character.name}</div>
              
              <button 
                className={styles.toggleButton}
                onClick={() => handleToggleDetails(character.id)}
              >
                {expandedCharacter === character.id ? '▲' : '▼'}
              </button>
            </div>
            
            <div className={`${styles.characterDetails} ${expandedCharacter === character.id ? styles.expanded : styles.collapsed}`}>
              <div className={styles.detailSection}>
                <h3>性格</h3>
                <p>{character.personality}</p>
              </div>
              
              <div className={styles.detailSection}>
                <h3>口調</h3>
                <p>{character.speech_pattern}</p>
              </div>
              
              <div className={styles.detailSection}>
                <h3>得意な話題</h3>
                <p>{character.interests}</p>
              </div>
              
              <div className={styles.detailSection}>
                <h3>特徴</h3>
                <p>{character.traits}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <button 
        className={styles.startButton}
        onClick={handleStartEvent}
        disabled={!selectedCharacter}
      >
        イベント開始
      </button>
    </div>
  );
};

export default CharacterSelect;