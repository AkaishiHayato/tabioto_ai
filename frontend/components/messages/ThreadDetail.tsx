"use client";

import { useEffect, useState } from "react";
import { getThread, sendMessage, setSkipAutoReply } from "@/lib/messages-client";
import type { Message, MessageThread } from "@/lib/types";
import { MessageBubble } from "./MessageBubble";
import { ReplyComposer } from "./ReplyComposer";
import {
  isPlaceholderGuestMessage,
  resolveErrorMessage,
  sortMessagesAscending,
} from "./utils";

type Props = {
  airbnbThreadId: string;
  // 一覧側の該当行(プレビュー・自動返信停止フラグ等)を最新状態に同期するための通知
  onThreadUpdate: (thread: MessageThread) => void;
};

export function ThreadDetail({ airbnbThreadId, onThreadUpdate }: Props) {
  const [thread, setThread] = useState<MessageThread | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [togglingSkip, setTogglingSkip] = useState(false);
  const [replyText, setReplyText] = useState("");

  async function fetchThread() {
    setLoading(true);
    setError(null);
    try {
      const data = await getThread(airbnbThreadId);
      setThread(data.thread);
      setMessages(data.messages);
      onThreadUpdate(data.thread);
    } catch (e) {
      setError(resolveErrorMessage(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // 親コンポーネントが ThreadDetail に key={airbnbThreadId} を付けているため、
    // スレッド切替時はコンポーネント自体が再マウントされ state は初期値に戻る。
    // ここではマウント時に一度だけ取得すればよい。
    // REST API (getThread) をイベント起点(自動返信停止トグル・送信後)でも
    // 再利用する都合上 Suspense/use() ベースには載せず、素直な effect フェッチを行う。
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchThread();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [airbnbThreadId]);

  async function handleToggleSkip() {
    if (!thread || togglingSkip) return;
    setTogglingSkip(true);
    try {
      const updated = await setSkipAutoReply(
        airbnbThreadId,
        !thread.skip_auto_reply,
      );
      setThread(updated);
      onThreadUpdate(updated);
    } catch (e) {
      setError(resolveErrorMessage(e));
    } finally {
      setTogglingSkip(false);
    }
  }

  async function handleSend(text: string) {
    await sendMessage(airbnbThreadId, text);
    setReplyText("");
    await fetchThread();
  }

  const sortedMessages = sortMessagesAscending(messages);

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between gap-4 border-b border-zinc-200 p-4 dark:border-zinc-800">
        <div className="min-w-0">
          <h2 className="truncate text-base font-semibold text-zinc-900 dark:text-zinc-100">
            {thread?.guest_name ?? thread?.thread_title ?? "スレッド"}
          </h2>
          {thread?.reservation_status && (
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              {thread.reservation_status}
            </p>
          )}
        </div>
        {thread && (
          <label className="flex shrink-0 items-center gap-2 text-sm text-zinc-600 dark:text-zinc-300">
            <span>このスレッドの自動返信を停止</span>
            <input
              type="checkbox"
              checked={thread.skip_auto_reply}
              disabled={togglingSkip}
              onChange={handleToggleSkip}
              className="h-4 w-4 accent-zinc-900 dark:accent-zinc-100"
            />
          </label>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {loading && (
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            読み込み中...
          </p>
        )}
        {error && (
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        )}
        {!loading && !error && sortedMessages.length === 0 && (
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            メッセージがありません
          </p>
        )}
        {!loading && !error && sortedMessages.length > 0 && (
          <div className="flex flex-col gap-4">
            {sortedMessages.map((m) => (
              <div key={m.id} className="flex flex-col gap-2">
                {!isPlaceholderGuestMessage(m.guest_message) && (
                  <MessageBubble
                    align="left"
                    text={m.guest_message}
                    timestamp={m.received_at ?? m.created_at}
                  />
                )}
                {m.reply_text && (
                  <MessageBubble
                    align="right"
                    text={m.reply_text}
                    timestamp={m.processed_at ?? m.received_at ?? m.created_at}
                    label={
                      m.status === "auto_replied"
                        ? "Ava(自動返信)"
                        : m.status === "manual_replied"
                          ? "手動返信"
                          : undefined
                    }
                    onEdit={() => setReplyText(m.reply_text ?? "")}
                  />
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <ReplyComposer
        value={replyText}
        onChange={setReplyText}
        onSubmit={handleSend}
        disabled={loading}
      />
    </div>
  );
}
