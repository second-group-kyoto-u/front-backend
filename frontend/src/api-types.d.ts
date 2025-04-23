// スレッド関連API型定義
declare module '@/api/thread' {
  export interface Thread {
    id: string;
    title: string;
    created_at: string;
    created_by: {
      user_name: string;
    };
    tags: Array<{
      id: string;
      name: string;
    }>;
    hearts_count: number;
    messages_count: number;
  }

  export interface ThreadDetailResponse {
    thread: {
      id: string;
      title: string;
      created_at: string;
      created_by: {
        user_name: string;
      };
      tags: Array<{
        id: string;
        name: string;
      }>;
      hearts_count: number;
      is_hearted: boolean;
    };
    messages: Array<{
      id: string;
      content: string;
      message_type: 'text' | 'image';
      created_at: string;
      created_by: {
        user_name: string;
      };
    }>;
  }

  export function getThreads(params: { page: number; per_page: number }): Promise<{ threads: Thread[]; total: number }>;
  export function getThreadDetail(threadId: string, token: string): Promise<ThreadDetailResponse>;
  export function postMessage(threadId: string, data: { content: string; message_type: string }, token: string): Promise<any>;
  export function heartThread(threadId: string, token: string): Promise<any>;
  export function unheartThread(threadId: string, token: string): Promise<any>;
  export function createThread(data: any): Promise<{ thread_id: string }>;
}

// 画像アップロードAPI型定義
declare module '@/api/upload' {
  export function uploadImage(file: File, token?: string): Promise<{ image: { id: string } }>;
} 