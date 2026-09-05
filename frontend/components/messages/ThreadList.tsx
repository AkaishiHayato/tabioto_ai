import type { MessageThread } from "@/lib/types";
import { formatDateTime } from "./utils";

type Props = {
  threads: MessageThread[];
  selectedThreadId: string | null;
  onSelect: (airbnbThreadId: string) => void;
};

export function ThreadList({ threads, selectedThreadId, onSelect }: Props) {
  if (threads.length === 0) {
    return (
      <p className="p-4 text-sm text-zinc-500 dark:text-zinc-400">
        スレッドがありません
      </p>
    );
  }

  return (
    <ul className="flex-1 overflow-y-auto">
      {threads.map((thread) => {
        const isSelected = thread.airbnb_thread_id === selectedThreadId;
        const needsReply = thread.last_sender_role === "guest";

        return (
          <li key={thread.id}>
            <button
              type="button"
              onClick={() => onSelect(thread.airbnb_thread_id)}
              className={`flex w-full flex-col gap-1 border-b border-zinc-100 px-4 py-3 text-left transition-colors dark:border-zinc-900 ${
                isSelected
                  ? "bg-zinc-100 dark:bg-zinc-900"
                  : "hover:bg-zinc-50 dark:hover:bg-zinc-950"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="truncate text-sm font-medium text-zinc-900 dark:text-zinc-100">
                  {thread.guest_name ?? thread.thread_title ?? "(名称未設定)"}
                </span>
                {needsReply && (
                  <span className="shrink-0 rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-700 dark:bg-red-950 dark:text-red-300">
                    要返信
                  </span>
                )}
              </div>
              <p className="truncate text-xs text-zinc-500 dark:text-zinc-400">
                {thread.last_message_preview ?? ""}
              </p>
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs text-zinc-400 dark:text-zinc-500">
                  {formatDateTime(thread.last_message_at)}
                </span>
                {thread.skip_auto_reply && (
                  <span className="shrink-0 rounded-full bg-zinc-200 px-2 py-0.5 text-xs text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
                    自動返信停止中
                  </span>
                )}
              </div>
            </button>
          </li>
        );
      })}
    </ul>
  );
}
