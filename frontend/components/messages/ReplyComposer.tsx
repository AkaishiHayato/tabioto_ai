"use client";

import { useState } from "react";

type Props = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (text: string) => Promise<void>;
  disabled?: boolean;
};

export function ReplyComposer({ value, onChange, onSubmit, disabled }: Props) {
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    const trimmed = value.trim();
    if (!trimmed || sending || disabled) return;

    setSending(true);
    setError(null);
    try {
      await onSubmit(trimmed);
    } catch (e) {
      setError(e instanceof Error ? e.message : "送信に失敗しました");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="border-t border-zinc-200 p-4 dark:border-zinc-800">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled || sending}
        rows={3}
        placeholder="Avaとして返信するメッセージを入力..."
        className="w-full resize-none rounded-md border border-zinc-300 bg-white p-3 text-sm text-zinc-900 focus:border-zinc-500 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
      />
      {error && (
        <p className="mt-2 text-sm text-red-600 dark:text-red-400">{error}</p>
      )}
      <div className="mt-2 flex justify-end">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={disabled || sending || !value.trim()}
          className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
        >
          {sending ? "送信中..." : "Avaとして返信"}
        </button>
      </div>
    </div>
  );
}
