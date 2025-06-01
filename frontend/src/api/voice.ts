import axios from '@/lib/axios';

export interface VoiceChatRequest {
  character_id: string;
  audio_data: string; // base64 encoded audio
  event_id: string;
  location?: {
    latitude: number;
    longitude: number;
  };
  weather_info?: any;
}

export interface VoiceChatResponse {
  response_text: string;
  audio_data: string; // base64 encoded audio response
  character_id: string;
  debug_info?: {
    intent_analysis: {
      needs_weather: boolean;
      needs_location: boolean;
      analysis_reason: {
        weather_match: string[];
        location_match: string[];
      };
    };
    weather_used: boolean;
    location_used: boolean;
  };
}

export const startVoiceChat = async (request: VoiceChatRequest): Promise<VoiceChatResponse> => {
  try {
    // 音声チャット専用の延長タイムアウト（90秒）
    const response = await axios.post('/voice/chat', request, {
      timeout: 90000  // 音声処理（Whisper + AI分析 + 天気API + 場所API + ChatGPT + TTS）
    });
    return response.data;
  } catch (error: any) {
    // エラーレスポンスがある場合は、そのメッセージを使用
    if (error.response?.data?.error) {
      throw new Error(error.response.data.error);
    }
    // その他のエラー
    throw new Error(error.message || '音声チャットAPIエラー');
  }
}; 