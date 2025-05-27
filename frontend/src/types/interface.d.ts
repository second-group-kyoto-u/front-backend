import { EventMessageType as OriginalEventMessageType } from '@/api/event';

// EventMessageTypeを拡張
export interface ExtendedEventMessageType extends OriginalEventMessageType {
  sender_user_id?: string;
} 