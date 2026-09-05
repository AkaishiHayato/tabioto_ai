// メッセージページ専用の小ユーティリティ群。
import { ApiError } from "@/lib/api";
import type { Message } from "@/lib/types";

// API呼び出し失敗時にユーザー向けに表示するエラーメッセージへ変換する。
// 401はAirbnbセッション切れ、それ以外のApiErrorは一般的なAPIエラー、
// それ以外(fetch自体の失敗などバックエンド未起動時)はネットワークエラーとして扱う。
export function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return "Airbnbセッションが切れています。再度ログインしてください。";
    }
    return `エラーが発生しました (${error.status}): ${error.message}`;
  }
  return "バックエンドに接続できませんでした。しばらくしてから再度お試しください。";
}

export function formatDateTime(value: string | null): string {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleString("ja-JP", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// 手動送信された行は guest_message に「(補助ホスト手動送信)」のような
// ダミー文言が入る場合がある。その場合はゲスト側吹き出しを描画しないため判定する。
export function isPlaceholderGuestMessage(text: string): boolean {
  const trimmed = text.trim();
  if (!trimmed) return true;
  const isBracketed =
    (trimmed.startsWith("(") && trimmed.endsWith(")")) ||
    (trimmed.startsWith("（") && trimmed.endsWith("）"));
  return isBracketed && trimmed.includes("手動送信");
}

// APIは新しい順で返るため、表示用に received_at 昇順(古い順)へ並び替える。
// received_at が無い場合は created_at をフォールバックに使う。
export function sortMessagesAscending(messages: Message[]): Message[] {
  return [...messages].sort((a, b) => {
    const aTime = new Date(a.received_at ?? a.created_at).getTime();
    const bTime = new Date(b.received_at ?? b.created_at).getTime();
    return aTime - bTime;
  });
}
