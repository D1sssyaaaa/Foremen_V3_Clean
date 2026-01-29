export interface Notification {
  id: number;
  user_id: number;
  notification_type: string;
  title: string;
  message: string;
  data: Record<string, any> | null;
  is_read: boolean;
  status: 'pending' | 'sent' | 'delivered' | 'failed';
  telegram_message_id: number | null;
  telegram_chat_id: number | null;
  created_at: string;
  sent_at: string | null;
  read_at: string | null;
}

export interface NotificationBadge {
  unread_count: number;
  latest_notifications: Notification[];
}
