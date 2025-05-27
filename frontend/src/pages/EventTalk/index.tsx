import React, { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { sendEventMessage, getEvent, startEvent, endEvent, getCharacter, getEventWeatherInfo, getAdvisorResponse, getCharacters } from '@/api/event'
import { uploadImage } from '@/api/upload'
import { useAuth } from '@/hooks/useAuth'
import type { EventType } from '@/api/event'
import type { ExtendedEventMessageType } from '@/types/interface'
import styles from './EventTalk.module.css'
import CharacterSelect from './components/CharacterSelect'

// キャラクターごとのデフォルト会話内容
const DEFAULT_CHARACTER_MESSAGES = {
  'nyanta': {
    greeting: 'ふーん、こんにちは。今日のイベントガイドを担当することになったニャンタだよ。なんでこの仕事を引き受けたのかは自分でもよくわからないけど...まぁ、せっかくだし楽しく過ごそうニャ。何か知りたいことがあったら聞いてみて。答えられるかどうかは気分次第だけどね。',
    weather_info: ''
  },
  'hitsuji': {
    greeting: 'こんにちは～。本日のイベントガイドを務めさせていただくヒツジと申します。皆さんのお役に立てるよう、精一杯サポートしますので、どうぞよろしくお願いします～。素敵な思い出作りのお手伝いができれば嬉しいです。何か質問があれば、お気軽にお声がけくださいね～。一緒に楽しい時間を過ごしましょう～。',
    weather_info: ''
  },
  'koko': {
    greeting: 'やっほー！今日のイベントガイド担当のココだよ！わぁ、こんなに素敵な場所でイベントできるなんて最高じゃない！？どんなことして遊ぶ？何食べる？どこ行く？なんでも聞いてね！めっちゃ楽しい思い出作りましょ！ワクワクが止まらないよ～！一緒に最高の時間にしようね！',
    weather_info: ''
  },
  'fukurou': {
    greeting: 'ようこそ。本日のイベントにてガイドを務めますフクロウと申します。皆様の楽しく、かつ有意義な時間となるよう、知識と情報をご提供いたします。イベントを最大限に楽しむためのコツは、好奇心を持ち、新しい発見を大切にすることです。ご質問やお手伝いが必要な際は、どうぞお気軽にお声がけください。充実したひとときをお過ごしいただけるよう、精一杯サポートいたします。',
    weather_info: ''
  },
  'toraberu': {
    greeting: 'よっしゃー！今日のイベントガイドを任されたトラベルだぜ！最高に楽しい冒険の始まりだな！みんなで素晴らしい体験をしようぜ！困ったことがあったら何でも言ってくれ！とりあえず、笑顔でいくことが一番大事！今日は思いっきり楽しもうぜ！エネルギー全開で行くぞー！',
    weather_info: ''
  }
};

function EventTalkPage() {
  const { eventId } = useParams<{ eventId: string }>()
  const { token } = useAuth()
  const navigate = useNavigate()
  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const [eventData, setEventData] = useState<EventType | null>(null)
  const [messages, setMessages] = useState<ExtendedEventMessageType[]>([])
  const [newMessage, setNewMessage] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedFilePreview, setSelectedFilePreview] = useState<string | null>(null)
  const [sending, setSending] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isAuthor, setIsAuthor] = useState(false)
  const [isSendingTrivia, setIsSendingTrivia] = useState(false)
  const [userLocation, setUserLocation] = useState<{latitude: number, longitude: number} | null>(null)
  const [selectedCharacter, setSelectedCharacter] = useState<string | null>(null)
  const [characterData, setCharacterData] = useState<any>(null)
  const [showCharacterModal, setShowCharacterModal] = useState(false)
  const [isAdviserMode, setIsAdviserMode] = useState(false)
  const [characterList, setCharacterList] = useState<{id: string, name: string}[]>([
    {id: 'nyanta', name: 'ニャンタ'},
    {id: 'hitsuji', name: 'ヒツジ'},
    {id: 'koko', name: 'ココ'},
    {id: 'fukurou', name: 'フクロウ'},
    {id: 'toraberu', name: 'トラベル'}
  ]);
  const [showMenu, setShowMenu] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    if (messages.length > 0) {
      scrollToBottom()
    }
  }, [messages])

  useEffect(() => {
    if (eventId) {
      fetchMessages()
      // 定期的な更新（30秒ごと）
      const intervalId = setInterval(fetchMessages, 30000)
      return () => clearInterval(intervalId)
    }
  }, [eventId])
  
  // キャラクター選択情報の取得
  useEffect(() => {
    const character = sessionStorage.getItem('selectedCharacter')
    if (character) {
      console.log('保存されたキャラクター情報を取得:', character);
      setSelectedCharacter(character)
      fetchCharacterData(character)
      // イベント開始直後の場合のボットメッセージは送信しない
      // バックエンドが既にメッセージを生成しているため
      setShowCharacterModal(false)
    } else {
      setShowCharacterModal(true)
    }
  }, [eventData, messages.length])

  // キャラクター情報の取得
  const fetchCharacterData = async (characterId: string) => {
    try {
      console.log('キャラクター情報の取得を開始:', characterId);
      const response = await getCharacter(characterId);
      console.log('キャラクターAPI応答:', response);
      
      if (response && response.character) {
        setCharacterData(response.character);
        
        // キャラクタープロパティの確認とログ出力
        if (response.character.avatar_url) {
          console.log('キャラクターアバターURL:', response.character.avatar_url);
        } else {
          console.warn('キャラクターにアバターURLが設定されていません');
        }
      } else {
        console.error('キャラクター情報が不完全です:', response);
      }
    } catch (err) {
      console.error('キャラクター情報取得エラー:', err);
    }
  }

  // デフォルトの挨拶メッセージを追加
  const addDefaultGreeting = async (characterId: string) => {
    if (!eventId || !characterId) {
      console.error('addDefaultGreeting: イベントIDまたはキャラクターIDがありません', { eventId, characterId });
      return;
    }
    
    console.log('デフォルト挨拶を追加します', { characterId, messageCount: messages.length });
    
    // メッセージの中にすでにbotメッセージが含まれているか確認
    const hasBotMessages = messages.some(msg => msg.message_type === 'bot');
    
    // すでにbotメッセージがある場合は、追加の挨拶を送信しない
    if (hasBotMessages) {
      console.log('既にbotメッセージが存在するため、デフォルト挨拶をスキップします');
      return;
    }
    
    const defaultMessage = DEFAULT_CHARACTER_MESSAGES[characterId as keyof typeof DEFAULT_CHARACTER_MESSAGES]?.greeting;
    
    if (defaultMessage) {
      console.log('デフォルト挨拶メッセージを表示します:', characterId, defaultMessage);
      
      try {
        // サーバーにメッセージを送信
        await sendEventMessage(eventId, { 
          content: defaultMessage, 
          message_type: `bot_${characterId}`,
          metadata: { character_id: characterId }  // キャラクターIDをメタデータとして送信
        });
        
        // メッセージの再読み込み
        await fetchMessages();
        
        // 非同期で天気情報を取得して表示
        fetchWeatherInfo(characterId);
      } catch (error) {
        console.error('挨拶メッセージの送信に失敗しました:', error);
        
        // APIエラー時はローカルで表示（フォールバック）
        const botGreeting: ExtendedEventMessageType = {
          id: `default-greeting-${Date.now()}`,
          event_id: eventId,
          content: defaultMessage,
          message_type: `bot_${characterId}`,
          timestamp: new Date().toISOString(),
          sender_user_id: undefined,
          sender: null,
          image_url: null,
          metadata: { character_id: characterId },
          read_count: 0
        };
        
        setMessages(prevMessages => [...prevMessages, botGreeting]);
      }
    } else {
      console.error('デフォルトメッセージが見つかりません:', characterId);
    }
  }

  // 天気情報を取得して表示
  const fetchWeatherInfo = async (characterId: string) => {
    if (!eventId) {
      console.error('fetchWeatherInfo: イベントIDがありません');
      return;
    }

    // メッセージの中に既に天気情報を含むbotメッセージがあるか確認
    const hasWeatherMessages = messages.some(msg => 
      msg.message_type === 'bot' && 
      (msg.content?.includes('今日の天気は') || msg.content?.includes('お天気は'))
    );
    
    // 既に天気情報メッセージがある場合は、追加の天気情報を送信しない
    if (hasWeatherMessages) {
      console.log('既に天気情報メッセージが存在するため、天気情報の取得をスキップします');
      return;
    }

    console.log('天気情報取得を開始します', { characterId, eventId });

    try {
      // 位置情報を取得
      let location: { latitude: number; longitude: number } | undefined = undefined;
      if (navigator.geolocation) {
        try {
          console.log('位置情報の取得を開始します');
          const position = await new Promise<GeolocationPosition>((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, {
              timeout: 8000,  // 位置情報取得のタイムアウトを8秒に設定（より長く）
              maximumAge: 60000
            });
          });
          
          location = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
          };
          console.log('位置情報の取得に成功しました', location);
          setUserLocation(location);
        } catch (error) {
          console.error('位置情報の取得に失敗しました:', error);
        }
      }

      // 天気情報を取得（タイムアウト制御を追加）
      console.log('天気情報APIを呼び出します', { eventId, location });
      
      // タイムアウト用のPromiseを作成
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('天気情報の取得がタイムアウトしました')), 10000);
      });
      
      // 天気情報取得のPromise
      const weatherPromise = getEventWeatherInfo(eventId, location ? { location } : undefined);
      
      // Promise.raceでタイムアウト制御
      const weatherData = await Promise.race([weatherPromise, timeoutPromise]) as any;
      
      console.log('天気情報の取得に成功しました', weatherData);
      
      // キャラクターのスタイルに合わせて天気情報とアドバイスを整形
      let weatherMessage = '';
      
      if (weatherData && weatherData.weather_info) {
        const { weather, temp, feels_like } = weatherData.weather_info;
        const advice = weatherData.advice || '';
        
        console.log('天気情報を整形します', { weather, temp, feels_like, advice });
        
        // キャラクターごとの口調に合わせたメッセージを作成
        if (characterId === 'nyanta') {
          weatherMessage = `ところでニャ、今日の天気は「${weather}」だよ。気温は${temp}℃くらいで体感温度は${feels_like}℃くらいだニャ。${advice}...まぁ、参考になれば良いんじゃない？`;
        } else if (characterId === 'hitsuji') {
          weatherMessage = `あの～、今日のお天気は「${weather}」ですよ～。気温は${temp}℃で、体感温度は${feels_like}℃くらいです～。${advice}　皆さんが快適に過ごせますように～。`;
        } else if (characterId === 'koko') {
          weatherMessage = `あっ！今日の天気チェックしたよ！「${weather}」だって！気温は${temp}℃で体感は${feels_like}℃！${advice}　楽しい時間にしようね～！`;
        } else if (characterId === 'fukurou') {
          weatherMessage = `本日の気象情報をお知らせいたします。現在の天気は「${weather}」、気温は${temp}℃（体感温度${feels_like}℃）です。${advice}　どうぞ参考になさってください。`;
        } else if (characterId === 'toraberu') {
          weatherMessage = `よっしゃ！今日の天気は「${weather}」だ！気温は${temp}℃で体感温度は${feels_like}℃くらいだぜ！${advice}　さあ、元気に行こうぜ！`;
        } else {
          weatherMessage = `今日の天気は「${weather}」です。気温は${temp}℃（体感温度${feels_like}℃）です。${advice}`;
        }
        
        // 天気情報メッセージをキャラクターのデフォルトメッセージに保存
        if (characterId in DEFAULT_CHARACTER_MESSAGES) {
          DEFAULT_CHARACTER_MESSAGES[characterId as keyof typeof DEFAULT_CHARACTER_MESSAGES].weather_info = weatherMessage;
        }
        
        // 天気情報メッセージを表示
        console.log('天気情報メッセージを送信します', weatherMessage);
        
        // 少し遅延させて送信することで会話感を出す
        setTimeout(async () => {
          try {
            await sendEventMessage(eventId, { 
              content: weatherMessage, 
              message_type: `bot_${characterId}`,  // 「bot_キャラクターID」の形式に変更
              metadata: { character_id: characterId }
            });
            
            // メッセージの再読み込み
            await fetchMessages();
          } catch (error) {
            console.error('天気情報メッセージの送信に失敗しました:', error);
            
            // APIエラー時はローカルで表示（フォールバック）
            const weatherBotMessage: ExtendedEventMessageType = {
              id: `weather-info-${Date.now()}`,
              event_id: eventId,
              content: weatherMessage,
              message_type: `bot_${characterId}`,  // 「bot_キャラクターID」の形式に変更
              timestamp: new Date().toISOString(),
              sender_user_id: undefined,
              sender: null,
              image_url: null,
              metadata: { character_id: characterId },
              read_count: 0
            };
            
            setMessages(prevMessages => [...prevMessages, weatherBotMessage]);
          }
        }, 2000);
      } else {
        console.warn('天気情報を取得できませんでした（データなし）');
      }
    } catch (error) {
      console.error('天気情報の取得に失敗しました:', error);
      // エラー時にもフォールバックメッセージを表示
      try {
        // フォールバックの天気メッセージ
        const fallbackMessage = `季節や時間に合わせた服装で、イベントをお楽しみください。水分補給を忘れずに、快適な時間をお過ごしください。`;
        
        // キャラクターごとの口調に合わせたフォールバックメッセージ
        let weatherMessage = '';
        if (characterId === 'nyanta') {
          weatherMessage = `そういえばニャ、外を歩くなら${fallbackMessage}...まぁ、気にしなくてもいいけどね。`;
        } else if (characterId === 'hitsuji') {
          weatherMessage = `あの～、お出かけの際は${fallbackMessage}皆さんが快適に過ごせますように～。`;
        } else if (characterId === 'koko') {
          weatherMessage = `そうそう、思い出した！${fallbackMessage}楽しい時間にしようね～！`;
        } else if (characterId === 'fukurou') {
          weatherMessage = `イベントを最大限お楽しみいただくため、${fallbackMessage}どうぞご参考になさってください。`;
        } else if (characterId === 'toraberu') {
          weatherMessage = `そうだ！大事なこと言い忘れてた！${fallbackMessage}さあ、元気に行こうぜ！`;
        } else {
          weatherMessage = fallbackMessage;
        }
        
        // サーバーにフォールバックメッセージを送信
        try {
          await sendEventMessage(eventId, { 
            content: weatherMessage, 
            message_type: `bot_${characterId}`,  // 「bot_キャラクターID」の形式に変更
            metadata: { character_id: characterId }
          });
          
          // メッセージの再読み込み
          await fetchMessages();
        } catch (sendError) {
          console.error('フォールバックメッセージの送信に失敗しました:', sendError);
          
          // APIエラー時はローカルで表示（フォールバック）
          const fallbackBotMessage: ExtendedEventMessageType = {
            id: `weather-fallback-${Date.now()}`,
            event_id: eventId,
            content: weatherMessage,
            message_type: `bot_${characterId}`,  // 「bot_キャラクターID」の形式に変更
            timestamp: new Date().toISOString(),
            sender_user_id: undefined,
            sender: null,
            image_url: null,
            metadata: { character_id: characterId },
            read_count: 0
          };
          
          setMessages(prevMessages => [...prevMessages, fallbackBotMessage]);
        }
      } catch (fallbackError) {
        console.error('フォールバックメッセージの表示にも失敗しました:', fallbackError);
      }
    }
  };

  // 選択されたファイルがある場合、プレビューを生成
  useEffect(() => {
    if (selectedFile) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setSelectedFilePreview(reader.result as string);
      };
      reader.readAsDataURL(selectedFile);
    } else {
      setSelectedFilePreview(null);
    }
  }, [selectedFile]);

  const fetchMessages = async () => {
    if (!eventId) return
    setLoading(true)
    try {
      console.log('イベントメッセージを取得します...');
      const data = await getEvent(eventId)
      setEventData(data.event)
      
      // メッセージにsender_user_idを追加
      const processedMessages = data.messages.map((msg: any) => ({
        ...msg,
        sender_user_id: msg.sender?.id
      }));
      
      console.log('イベントメッセージ取得完了:', {
        count: processedMessages.length,
        currentCount: messages.length,
        status: data.event?.status
      });
      
      // 既存メッセージがない場合、または取得したメッセージが空でない場合にのみ更新
      // ただし挨拶メッセージだけの場合には上書きしない
      if (messages.length === 0 || 
          (processedMessages.length > 0 && 
           !(messages.length === 1 && messages[0].id.startsWith('default-greeting')))) {
        setMessages(processedMessages)
      } else {
        console.log('デフォルトメッセージを保持するため更新をスキップします');
      }
      
      // 自分がイベント作成者かチェック
      if (token && data.event && data.event.author) {
        const currentUserId = getUserIdFromToken(token)
        setIsAuthor(currentUserId === data.event.author.id)
      }
    } catch (err: any) {
      console.error('メッセージ取得エラー:', err)
      setError('メッセージの取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  // イベント開始
  const handleStartEvent = async () => {
    if (!eventId || !token) return
    
    // キャラクター選択モーダルを表示
    setShowCharacterModal(true)
  }
  
  // イベント終了
  const handleEndEvent = async () => {
    if (!eventId || !token) return
    
    try {
      setSending(true)
      await endEvent(eventId)
      await fetchMessages()
    } catch (err: any) {
      console.error('イベント終了エラー:', err)
      setError('イベントの終了に失敗しました')
    } finally {
      setSending(false)
    }
  }

  // handleSubmitメソッドを修正して、エンターキー固有のロジックを追加
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!eventId || !token) {
      setError('ログインが必要です')
      return
    }
    if ((!selectedFile && !newMessage.trim()) || sending) return

    setSending(true)
    setError('')
    setUploadProgress(0)
    
    try {
      if (selectedFile) {
        // ファイルサイズチェック（5MB制限）
        if (selectedFile.size > 5 * 1024 * 1024) {
          throw new Error('画像サイズは5MB以下にしてください')
        }
        
        // 画像送信
        setUploadProgress(10)
        const uploadRes = await uploadImage(selectedFile, token)
        setUploadProgress(70)
        
        if (!uploadRes || !uploadRes.image || !uploadRes.image.id) {
          throw new Error('画像のアップロードに失敗しました')
        }
        
        // イベントメッセージとして画像IDを送信
        await sendEventMessage(eventId, { 
          image_id: uploadRes.image.id, 
          message_type: 'image' 
        })
        setUploadProgress(100)
        setSelectedFile(null)
        setSelectedFilePreview(null)
      } else if (newMessage.trim()) {
        if (isAdviserMode) {
          // アドバイザーモードの場合は、新しいAPIを呼び出す
          // 位置情報を取得
          let locationData: { latitude: number; longitude: number; } | undefined = undefined;
          if (userLocation) {
            locationData = {
              latitude: userLocation.latitude,
              longitude: userLocation.longitude
            };
          }
          
          // アドバイザー応答を取得
          await getAdvisorResponse(eventId, {
            message: newMessage.trim(),
            character_id: selectedCharacter || undefined,
            location: locationData
          });
          
        } else {
          // 通常のテキスト送信
          await sendEventMessage(eventId, { 
            content: newMessage.trim(), 
            message_type: 'text'
          });
        }
      }
      setNewMessage('')
      await fetchMessages()
    } catch (err: any) {
      console.error('送信エラー:', err)
      const errorMessage = err.response?.data?.message || err.message || 'メッセージ送信に失敗しました'
      setError(errorMessage)
    } finally {
      setSending(false)
      setUploadProgress(0)
    }
  }

  // 別のハンドラを追加してEnterキーを処理
  const handleTextareaKeyDown = (e: { key: string; shiftKey: boolean; preventDefault?: () => void }) => {
    if (e && e.key === 'Enter' && !e.shiftKey && e.preventDefault) {
      e.preventDefault();
      const fakeEvent = { preventDefault: () => {} } as React.FormEvent;
      handleSubmit(fakeEvent);
    }
  }

  const handleAttachClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null
    
    if (file) {
      // 画像タイプのチェック
      if (!file.type.startsWith('image/')) {
        setError('画像ファイルのみアップロードできます')
        return
      }
      
      // ファイルサイズのチェック
      if (file.size > 5 * 1024 * 1024) {
        setError('画像サイズは5MB以下にしてください')
        return
      }
      
      setSelectedFile(file)
      setError('')
    }
    
    // ファイル選択後に入力をリセット（同じファイルを選択可能にする）
    if (e.target) e.target.value = ''
  }

  const cancelFileSelection = () => {
    setSelectedFile(null)
    setSelectedFilePreview(null)
    setError('')
  }

  // ユーザー名の頭文字を取得（アバターに表示）
  const getUserInitial = (name: string | undefined): string => {
    if (!name) return '?'
    return name.charAt(0).toUpperCase()
  }

  // ユーザー名からアバターの背景色を生成
  const getUserColor = (name: string | undefined): string => {
    if (!name) return '#cccccc'
    const hash = name.split('').reduce((acc, char) => char.charCodeAt(0) + ((acc << 5) - acc), 0)
    const hue = Math.abs(hash) % 360
    return `hsl(${hue}, 70%, 80%)`
  }

  // ログイン中のユーザーがそのメッセージの送信者かどうか
  const isCurrentUser = (senderId: string | undefined): boolean => {
    if (!token || !senderId) return false
    // メッセージの送信者IDがログインユーザーのIDに一致する場合
    const currentUserId = getUserIdFromToken(token)
    return currentUserId !== undefined && currentUserId === senderId
  }

  // トークンからユーザーIDを取得
  const getUserIdFromToken = (token: string): string | undefined => {
    try {
      // JWTの2つ目のセグメント（ペイロード）をデコード
      const payload = token.split('.')[1]
      const decoded = JSON.parse(atob(payload))
      return decoded.user_id || undefined
    } catch (error) {
      return undefined
    }
  }

  // タイムスタンプをフォーマット（UTCからJSTに変換）
  const formatTimestamp = (timestamp: string | undefined): string => {
    if (!timestamp) return ''
    
    // UTCの日時を解析
    const date = new Date(timestamp)
    
    // 日本時間に設定（+9時間）
    const jstDate = new Date(date.getTime() + 9 * 60 * 60 * 1000)
    
    // 日本語形式で時刻を返す
    return jstDate.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' })
  }
  // 画像のレンダリング
  const renderImage = (imageUrl: string | null | undefined) => {
    if (typeof imageUrl === 'string' && imageUrl.trim() !== '') {
      return <img src={imageUrl} alt="投稿画像" loading="lazy" />
    }
    return <div className={styles.emptyImage}>画像を読み込めません</div>
  }

  // 位置情報を取得する
  const getUserLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
          })
        },
        (error) => {
          console.error('位置情報の取得に失敗しました:', error)
          // 豆知識生成時に再取得するので、ここではエラーメッセージを表示しない
        },
        { timeout: 10000, maximumAge: 60000 } // 10秒のタイムアウト、1分以内のキャッシュは許可
      )
    }
  }
  
  // コンポーネントマウント時に位置情報を取得
  useEffect(() => {
    getUserLocation()
  }, [])
  
  // 画像URLを処理する関数
  const processImageUrl = (url: string | null): string => {
    if (!url) return 'https://via.placeholder.com/50x50?text=User';
    
    // MinIOのURLを修正（内部ネットワークのURLを外部アクセス可能なURLに変換）
    if (url.includes(':9000/')) {
      // MinIOのURLの場合、nginxプロキシ経由に変換
      const urlParts = url.split(':9000/');
      if (urlParts.length === 2) {
        const newUrl = `http://${window.location.hostname}/minio/${urlParts[1]}`;
        return newUrl;
      }
    }
    
    return url;
  };

  // キャラクターリストを取得
  const fetchCharacterList = async () => {
    try {
      const response = await getCharacters();
      if (response && response.characters && Array.isArray(response.characters)) {
        setCharacterList(response.characters);
      }
    } catch (error) {
      console.error('キャラクターリスト取得エラー:', error);
      // エラー時はデフォルトリストを使用
    }
  };
  
  // useEffect内にキャラクターリスト取得を追加
  useEffect(() => {
    fetchCharacterList();
  }, []);

  // メニューを表示・非表示するトグル関数
  const toggleMenu = () => {
    setShowMenu(!showMenu);
  };

  // キャラクター変更関数を修正
  const changeCharacter = () => {
    // CharacterSelectモーダルを表示
    setShowCharacterModal(true);
    // メニューを閉じる
    setShowMenu(false);
  };

  // メッセージタイプからキャラクターIDを抽出する関数を追加
  const getCharacterIdFromMessageType = (messageType: string): string | null => {
    if (messageType && messageType.startsWith('bot_')) {
      return messageType.substring(4); // 'bot_' の後の部分を取得
    }
    return null;
  };

  // メッセージタイプがbotかどうかを判定する関数を修正
  const isBotMessage = (messageType: string | undefined): boolean => {
    if (!messageType) return false;
    return messageType === 'bot' || messageType.startsWith('bot_');
  };

  // 画面タップでメニューを閉じるために、コンポーネント全体にイベントリスナーを追加
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const menu = document.querySelector(`.${styles.menuDropdown}`);
      const menuButton = document.querySelector(`.${styles.menuButton}`);
      
      if (
        showMenu && 
        menu && 
        menuButton && 
        !menu.contains(event.target as Node) && 
        !menuButton.contains(event.target as Node)
      ) {
        setShowMenu(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showMenu, styles.menuDropdown, styles.menuButton]);

  if (loading && !messages.length) {
    return (
      <div className={styles.loadingSpinner}>
        読み込み中...
      </div>
    )
  }

  return (
    <div className={styles.pageContainer}>
      <div className={styles.header}>
        <button 
          className={styles.backButton} 
          onClick={() => navigate(`/event/${eventId}`)}
          aria-label="戻る"
        >
          ←
        </button>
        <h1 className={styles.title}>{eventData?.title || 'トークルーム'}</h1>
        <button className={styles.menuButton} aria-label="メニュー" onClick={toggleMenu}>⋮</button>
      </div>

      {/* イベント開始/終了ボタン（イベント作成者のみ表示） */}
      {isAuthor && eventData && (
        <div className={styles.eventControls}>
          {eventData.status === 'pending' && (
            <button 
              className={`${styles.eventControlButton} ${styles.startButton}`}
              onClick={handleStartEvent}
              disabled={sending}
            >
              <span className={styles.eventButtonIcon}>▶</span>
              イベントを開始する
            </button>
          )}
          
          {eventData.status === 'started' && (
            <button 
              className={`${styles.eventControlButton} ${styles.endButton}`}
              onClick={handleEndEvent}
              disabled={sending}
            >
              <span className={styles.eventButtonIcon}>■</span>
              イベントを終了する
            </button>
          )}
        </div>
      )}

      <div className={styles.messageList}>
        {error && <div className={styles.errorMessage}>{error}</div>}
        
        {messages.length === 0 && !loading && (
          <div className={styles.noMessages}>
            メッセージはまだありません。最初のメッセージを送信しましょう！
          </div>
        )}

        {messages.map((msg) => {
          if (msg.message_type === 'system') {
            // システムメッセージ
            return (
              <div key={msg.id} className={styles.systemMessage}>
                {msg.content}
              </div>
            );
          } else if (isBotMessage(msg.message_type)) {
            // botメッセージ
            // メッセージタイプまたはメタデータからキャラクターIDを取得
            const msgCharacterId = getCharacterIdFromMessageType(msg.message_type || '') || 
                                  (msg.metadata && msg.metadata.character_id) || 
                                  selectedCharacter || 
                                  'default';
            
            // キャラクター名の取得
            const characterName = characterList.find(c => c.id === msgCharacterId)?.name || msgCharacterId;
            const botName = `adviser ${characterName}`;
            
            // キャラクターのアバター画像URL
            const avatarUrl = 
              (characterData && characterData.avatar_url && msgCharacterId === selectedCharacter) ? 
              characterData.avatar_url : 
              null;
            
            return (
              <div key={msg.id} className={`${styles.botMessage} ${styles[`bot_${msgCharacterId}`] || ''}`}>
                <div className={styles.botMessageContainer}>
                  <div className={styles.botAvatar}>
                    {avatarUrl ? (
                      <img 
                        src={processImageUrl(avatarUrl)} 
                        alt={characterName} 
                        className={styles.botAvatarImage}
                        onError={(e: any) => {
                          console.error('ボットアバター画像の読み込みエラー:', avatarUrl);
                          const target = e.currentTarget as HTMLImageElement;
                          target.style.display = 'none';
                          if (target.parentElement) {
                            target.parentElement.textContent = msgCharacterId.charAt(0).toUpperCase();
                            target.parentElement.style.display = 'flex';
                            target.parentElement.style.justifyContent = 'center';
                            target.parentElement.style.alignItems = 'center';
                            target.parentElement.style.backgroundColor = '#e3f2fd';
                          }
                        }}
                      />
                    ) : (
                      <div className={styles.avatarPlaceholder}>
                        {msgCharacterId.charAt(0).toUpperCase()}
                      </div>
                    )}
                  </div>
                  <div className={styles.botContent}>
                    <div className={styles.botName}>{botName}</div>
                    <div>{msg.content}</div>
                    <div className={styles.botTimestamp}>{formatTimestamp(msg.timestamp || undefined)}</div>
                  </div>
                </div>
              </div>
            );
          } else {
            // 通常メッセージ
            return (
              <div 
                key={msg.id} 
                className={`${styles.messageItem} ${isCurrentUser(msg.sender_user_id) ? styles.sent : styles.received}`}
              >
                {/* アバター（自分のメッセージには表示しない） */}
                {!isCurrentUser(msg.sender_user_id) && (
                  <div 
                    className={styles.avatar}
                    style={{ backgroundColor: getUserColor(msg.sender?.user_name) }}
                  >
                    {msg.sender?.user_image_url ? (
                      <img 
                        src={msg.sender.user_image_url} 
                        alt={msg.sender.user_name} 
                        className={styles.userAvatarImage}
                        onError={(e: any) => {
                          const target = e.currentTarget as HTMLImageElement;
                          target.style.display = 'none';
                          target.parentElement!.textContent = getUserInitial(msg.sender?.user_name);
                        }}
                      />
                    ) : (
                      getUserInitial(msg.sender?.user_name)
                    )}
                  </div>
                )}

                <div className={`${styles.messageContent} ${isCurrentUser(msg.sender_user_id) ? styles.sent : ''}`}>
                  {/* 送信者名（自分のメッセージには表示しない） */}
                  {!isCurrentUser(msg.sender_user_id) && (
                    <div className={styles.senderName}>{msg.sender?.user_name || '不明なユーザー'}</div>
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
                  <div className={styles.timestamp}>{formatTimestamp(msg.timestamp || undefined)}</div>
                </div>
              </div>
            );
          }
        })}
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
          value={newMessage}
          onChange={(e: { target: { value: string } }) => setNewMessage(e.target.value)}
          placeholder="メッセージを入力"
          className={styles.messageInput}
          disabled={!!selectedFile || sending}
          onKeyDown={handleTextareaKeyDown}
        />
        <div className={styles.adviserContainer}>
          <div className={styles.adviserCheckboxContainer}>
            <input
              type="checkbox"
              id="adviserCheckbox"
              className={styles.adviserCheckbox}
              checked={isAdviserMode}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setIsAdviserMode(e.target.checked)}
            />
            <label htmlFor="adviserCheckbox" className={styles.adviserCheckboxLabel}>
              アドバイザーと会話
            </label>
          </div>
        </div>
        <button 
          type="submit" 
          className={styles.sendButton}
          disabled={(!newMessage.trim() && !selectedFile) || sending}
          aria-label="送信"
        >
          {sending ? '...' : '→'}
        </button>
      </form>

      {/* キャラクター選択モーダル */}
      {showCharacterModal && (
        <div className={styles.modalOverlay}>
          <div className={styles.modalContent}>
            <CharacterSelect 
              onSelect={() => {
                // モーダルを閉じる前にsessionStorageから最新のキャラクターIDを取得
                const selectedChar = sessionStorage.getItem('selectedCharacter');
                console.log('キャラクター選択完了（モーダル）:', selectedChar);
                
                if (selectedChar) {
                  const oldCharacter = selectedCharacter;
                  setSelectedCharacter(selectedChar);
                  fetchCharacterData(selectedChar);
                  
                  // モーダルをまず閉じる（UIをブロックしない）
                  setShowCharacterModal(false);
                  
                  // キャラクターが変更された場合、システムメッセージを表示
                  if (oldCharacter && oldCharacter !== selectedChar) {
                    // 変更前後のキャラクター名を取得
                    const oldCharName = characterList.find(c => c.id === oldCharacter)?.name || oldCharacter;
                    const newCharName = characterList.find(c => c.id === selectedChar)?.name || selectedChar;
                    
                    // 切り替えメッセージを表示
                    const switchMessage: ExtendedEventMessageType = {
                      id: `switch-message-${Date.now()}`,
                      event_id: eventId || '',
                      content: `アドバイザーを「${oldCharName}」から「${newCharName}」に変更しました`,
                      message_type: 'system',
                      timestamp: new Date().toISOString(),
                      sender_user_id: undefined,
                      sender: null,
                      image_url: null,
                      metadata: {},
                      read_count: 0
                    };
                    
                    setMessages(prevMessages => [...prevMessages, switchMessage]);
                  }
                  
                  // この時点で確実に挨拶を表示（条件なし）
                  console.log('強制的に挨拶を表示します');
                  
                  // 少し遅延させて挨拶を表示（イベント開始処理完了後）
                  setTimeout(() => {
                    console.log('遅延後の挨拶表示を開始');
                    // イベントのステータスを再確認
                    getEvent(eventId as string).then(data => {
                      console.log('イベントステータス確認:', data.event?.status);
                      // イベント開始済みの場合のみ表示
                      if (data.event?.status === 'started') {
                        console.log('イベント開始済み - 挨拶を表示します');
                        addDefaultGreeting(selectedChar);
                      } else {
                        console.log('イベント未開始のため挨拶を表示しません:', data.event?.status);
                      }
                    }).catch(err => {
                      console.error('イベントステータス確認エラー:', err);
                      // エラー時も挨拶だけは表示
                      addDefaultGreeting(selectedChar);
                    });
                  }, 1000);
                } else {
                  setShowCharacterModal(false);
                }
              }} 
              isModal={true} 
            />
          </div>
        </div>
      )}

      {/* メニュードロップダウン */}
      {showMenu && (
        <div className={styles.menuDropdown}>
          <div className={styles.menuItem} onClick={changeCharacter}>
            キャラクターを変更
          </div>
        </div>
      )}
    </div>
  )
}

export default EventTalkPage
