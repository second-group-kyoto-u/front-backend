import React, { useState, useRef, useEffect } from 'react';
import { startVoiceChat } from '@/api/voice';
import { getEventWeatherInfo } from '@/api/event';
import styles from './VoiceChat.module.css';

interface VoiceChatProps {
  characterId: string;
  eventId: string;
  onClose: () => void;
  characterName: string;
  characterAvatar?: string;
}

const VoiceChat: React.FC<VoiceChatProps> = ({
  characterId,
  eventId,
  onClose,
  characterName,
  characterAvatar
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [currentResponse, setCurrentResponse] = useState('');
  const [error, setError] = useState('');
  const [userLocation, setUserLocation] = useState<{ latitude: number; longitude: number } | null>(null);
  const [weatherInfo, setWeatherInfo] = useState<any>(null);
  const [isLocationInitialized, setIsLocationInitialized] = useState(false);
  const [lastLocationUpdate, setLastLocationUpdate] = useState<number>(0);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const locationUpdateIntervalRef = useRef<number | null>(null);

  useEffect(() => {
    // コンポーネント初期化時にオーディオコンテキストを作成
    const initAudioContext = async () => {
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
    };
    
    initAudioContext();
    
    // 初回の位置情報取得
    initializeLocationAndWeather();
    
    // 1分間隔で位置情報を更新
    locationUpdateIntervalRef.current = setInterval(() => {
      console.log('定期的な位置情報更新を実行します...');
      updateLocationPeriodically();
    }, 60000); // 60秒 = 1分
    
    return () => {
      // クリーンアップ
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      if (locationUpdateIntervalRef.current) {
        clearInterval(locationUpdateIntervalRef.current);
      }
    };
  }, []);

  const updateLocationPeriodically = async () => {
    try {
      console.log('位置情報の定期更新を開始...');
      
      if (navigator.geolocation) {
        const position = await new Promise<GeolocationPosition>((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, {
            timeout: 20000,  // 10000から20000に延長
            maximumAge: 0, // キャッシュを使わず常に新しい位置情報を取得
            enableHighAccuracy: true // より正確な位置情報を要求
          });
        });
        
        const newLocation = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude
        };
        
        // 位置が変わった場合のみ更新
        const hasLocationChanged = !userLocation || 
          Math.abs(userLocation.latitude - newLocation.latitude) > 0.0001 || 
          Math.abs(userLocation.longitude - newLocation.longitude) > 0.0001;
        
        if (hasLocationChanged) {
          console.log('位置情報が更新されました:', newLocation);
          setUserLocation(newLocation);
          setLastLocationUpdate(Date.now());
          
          // 位置が変わった場合は天気情報も更新
          try {
            console.log('位置変更により天気情報を更新中...');
            const weatherData = await getEventWeatherInfo(eventId, { location: newLocation });
            setWeatherInfo(weatherData);
            console.log('天気情報更新成功:', weatherData);
          } catch (weatherError) {
            console.error('天気情報の更新に失敗:', weatherError);
          }
        } else {
          console.log('位置情報に変更はありません');
        }
      }
    } catch (error) {
      console.error('定期的な位置情報更新に失敗:', error);
      // エラーが発生してもアプリケーションは継続
    }
  };

  const initializeLocationAndWeather = async () => {
    if (isLocationInitialized) {
      return; // 既に初期化済み
    }
    
    try {
      // 位置情報を取得
      if (navigator.geolocation) {
        console.log('初回の位置情報取得を開始します...');
        const position = await new Promise<GeolocationPosition>((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, {
            timeout: 20000,  // 10000から20000に延長
            maximumAge: 0, // キャッシュを使わず常に新しい位置情報を取得
            enableHighAccuracy: true // より正確な位置情報を要求
          });
        });
        
        const location = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude
        };
        
        setUserLocation(location);
        setLastLocationUpdate(Date.now());
        console.log('初回位置情報取得成功:', location);
        
        // 天気情報を取得
        try {
          console.log('初回天気情報を取得中...');
          const weatherData = await getEventWeatherInfo(eventId, { location });
          setWeatherInfo(weatherData);
          console.log('初回天気情報取得成功:', weatherData);
        } catch (weatherError) {
          console.error('初回天気情報の取得に失敗:', weatherError);
        }
        
        setIsLocationInitialized(true);
      }
    } catch (error) {
      console.error('初回位置情報の取得に失敗:', error);
      setIsLocationInitialized(true); // エラーでも初期化完了とする
    }
  };

  const startRecording = async () => {
    try {
      setError('');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await processAudio(audioBlob);
        
        // ストリームを停止
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (err) {
      console.error('マイクへのアクセスに失敗:', err);
      setError('マイクへのアクセスが拒否されました。ブラウザの設定を確認してください。');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const processAudio = async (audioBlob: Blob) => {
    try {
      setIsProcessing(true);
      
      // 初期化されていない場合のみ初期化
      if (!isLocationInitialized) {
        await initializeLocationAndWeather();
      }
      
      // Blobをbase64に変換
      const arrayBuffer = await audioBlob.arrayBuffer();
      const base64Audio = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));
      
      // 拡張されたリクエストデータを準備
      const requestData = {
        character_id: characterId,
        audio_data: base64Audio,
        event_id: eventId,
        location: userLocation || undefined,
        weather_info: weatherInfo
      };
      
      // APIに送信
      const response = await startVoiceChat(requestData);
      
      setCurrentResponse(response.response_text);
      
      // デバッグ情報をログ出力
      if (response.debug_info) {
        console.log('音声チャット分析結果:', response.debug_info);
      }
      
      // レスポンス音声を再生
      if (response.audio_data) {
        await playAudioResponse(response.audio_data);
      }
      
    } catch (err) {
      console.error('音声処理エラー:', err);
      setError(err instanceof Error ? err.message : '音声処理に失敗しました');
    } finally {
      setIsProcessing(false);
    }
  };

  const playAudioResponse = async (base64Audio: string) => {
    try {
      setIsPlaying(true);
      
      // base64を音声データに変換
      const binaryString = atob(base64Audio);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      
      const audioBlob = new Blob([bytes], { type: 'audio/mpeg' });
      const audioUrl = URL.createObjectURL(audioBlob);
      
      const audio = new Audio(audioUrl);
      audioRef.current = audio;
      
      audio.onended = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(audioUrl);
      };
      
      audio.onerror = () => {
        setIsPlaying(false);
        setError('音声の再生に失敗しました');
        URL.revokeObjectURL(audioUrl);
      };
      
      await audio.play();
      
    } catch (err) {
      console.error('音声再生エラー:', err);
      setError('音声の再生に失敗しました');
      setIsPlaying(false);
    }
  };

  const stopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
    }
  };

  return (
    <div className={styles.voiceChatOverlay}>
      <div className={styles.voiceChatModal}>
        <div className={styles.header}>
          <div className={styles.characterInfo}>
            {characterAvatar && (
              <img 
                src={characterAvatar} 
                alt={characterName} 
                className={styles.characterAvatar}
              />
            )}
            <h3 className={styles.characterName}>{characterName}と音声で会話</h3>
          </div>
          <button className={styles.closeButton} onClick={onClose}>×</button>
        </div>
        
        <div className={styles.topControls}>
          {!isRecording && !isProcessing && !isPlaying && (
            <button 
              className={styles.recordButton}
              onClick={startRecording}
            >
              <span className={styles.micIcon}>🎤</span>
              話しかける
            </button>
          )}
          
          {isRecording && (
            <button 
              className={styles.stopButton}
              onClick={stopRecording}
            >
              <span className={styles.stopIcon}>⏹️</span>
              録音停止
            </button>
          )}
          
          {isPlaying && (
            <button 
              className={styles.stopButton}
              onClick={stopAudio}
            >
              <span className={styles.stopIcon}>⏹️</span>
              再生停止
            </button>
          )}
        </div>
        
        <div className={styles.scrollableContent}>
          {error && (
            <div className={styles.error}>{error}</div>
          )}
          
          {userLocation && weatherInfo && (
            <div className={styles.infoArea}>
              <div className={styles.locationInfo}>
                📍 位置情報取得済み
                {lastLocationUpdate > 0 && (
                  <span className={styles.updateTime}>
                    (更新: {new Date(lastLocationUpdate).toLocaleTimeString()})
                  </span>
                )}
              </div>
              {weatherInfo.weather_info && (
                <div className={styles.weatherInfo}>
                  🌤️ {weatherInfo.weather_info.weather} {Math.round(weatherInfo.weather_info.temp)}℃
                </div>
              )}
            </div>
          )}
          
          <div className={styles.statusArea}>
            {isRecording && (
              <div className={styles.recordingStatus}>
                <div className={styles.recordingIndicator}></div>
                <span>録音中...</span>
              </div>
            )}
            
            {isProcessing && (
              <div className={styles.processingStatus}>
                <div className={styles.spinner}></div>
                <span>音声を処理中...</span>
              </div>
            )}
            
            {isPlaying && (
              <div className={styles.playingStatus}>
                <div className={styles.playingIndicator}></div>
                <span>{characterName}が話しています...</span>
              </div>
            )}
          </div>
          
          {currentResponse && (
            <div className={styles.responseArea}>
              <div className={styles.responseLabel}>{characterName}の返答:</div>
              <div className={styles.responseText}>{currentResponse}</div>
            </div>
          )}
          
          <div className={styles.instructions}>
            <p>マイクボタンを押して{characterName}に話しかけてください。</p>
            <p>位置情報と天気を考慮した返答をしてくれます。</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VoiceChat; 