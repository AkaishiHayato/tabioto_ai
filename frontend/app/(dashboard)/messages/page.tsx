"use client";

import { useEffect, useState } from "react";
import { listThreads } from "@/lib/messages-client";
import type { MessageThread } from "@/lib/types";
import { ThreadDetail } from "@/components/messages/ThreadDetail";
import { ThreadList } from "@/components/messages/ThreadList";
import { resolveErrorMessage } from "@/components/messages/utils";

export default function MessagesPage() {
  const [threads, setThreads] = useState<MessageThread[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(
    null,
  );

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await listThreads();
        if (cancelled) return;
        setThreads(data);
        setSelectedThreadId((prev) => prev ?? data[0]?.airbnb_thread_id ?? null);
      } catch (e) {
        if (cancelled) return;
        setError(resolveErrorMessage(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  function handleThreadUpdate(updated: MessageThread) {
    setThreads((prev) =>
      prev.map((t) =>
        t.airbnb_thread_id === updated.airbnb_thread_id ? updated : t,
      ),
    );
  }

  return (
    <div className="flex h-full">
      <div className="flex w-80 shrink-0 flex-col border-r border-zinc-200 dark:border-zinc-800">
        <div className="border-b border-zinc-200 p-4 dark:border-zinc-800">
          <h1 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            メッセージ
          </h1>
        </div>
        {loading && (
          <p className="p-4 text-sm text-zinc-500 dark:text-zinc-400">
            読み込み中...
          </p>
        )}
        {error && (
          <p className="p-4 text-sm text-red-600 dark:text-red-400">
            {error}
          </p>
        )}
        {!loading && !error && (
          <ThreadList
            threads={threads}
            selectedThreadId={selectedThreadId}
            onSelect={setSelectedThreadId}
          />
        )}
      </div>

      <div className="flex-1">
        {selectedThreadId ? (
          <ThreadDetail
            key={selectedThreadId}
            airbnbThreadId={selectedThreadId}
            onThreadUpdate={handleThreadUpdate}
          />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-zinc-500 dark:text-zinc-400">
            {!loading && !error && "スレッドを選択してください"}
          </div>
        )}
      </div>
    </div>
  );
}
